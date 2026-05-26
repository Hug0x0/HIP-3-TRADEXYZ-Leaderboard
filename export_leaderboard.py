#!/usr/bin/env python3
"""Export HIP-3 leaderboard addresses to CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://loris.tools/api/hip3-analytics/leaderboard"
DEFAULT_OUTPUT = "hip3_leaderboard_labels.csv"
DEFAULT_TIMEOUT = 30
DEFAULT_COLUMNS = ("label", "address")
AVAILABLE_COLUMNS = ("label", "address", "description")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export HIP-3 leaderboard addresses as label,address."
    )
    parser.add_argument("--period", default="all", help="API period parameter.")
    parser.add_argument("--sort-by", default="volume", help="API sort_by parameter.")
    parser.add_argument("--limit", type=int, default=500, help="Number of rows to request.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds. Default: {DEFAULT_TIMEOUT}",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"CSV output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--columns",
        default=",".join(DEFAULT_COLUMNS),
        help=(
            "Comma-separated CSV columns. "
            f"Available: {', '.join(AVAILABLE_COLUMNS)}. "
            f"Default: {','.join(DEFAULT_COLUMNS)}"
        ),
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Write CSV rows without the header line.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and summarize rows without writing the CSV file.",
    )
    return parser.parse_args()


def fetch_leaderboard(
    period: str,
    sort_by: str,
    limit: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[list[dict[str, Any]], int | None]:
    if limit < 1:
        raise RuntimeError("--limit must be at least 1")
    if timeout <= 0:
        raise RuntimeError("--timeout must be greater than 0")

    query = urlencode({"period": period, "sort_by": sort_by, "limit": limit})
    request = Request(
        f"{API_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "hip3-leaderboard-exporter/1.0",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"API returned HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("API response was not valid JSON") from exc

    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("API response did not contain a data list")

    total_traders = payload.get("total_traders")
    if not isinstance(total_traders, int):
        total_traders = None

    return [row for row in data if isinstance(row, dict)], total_traders


def parse_columns(raw_columns: str) -> list[str]:
    columns = [column.strip() for column in raw_columns.split(",") if column.strip()]
    if not columns:
        raise RuntimeError("--columns must include at least one column")

    invalid_columns = [column for column in columns if column not in AVAILABLE_COLUMNS]
    if invalid_columns:
        allowed = ", ".join(AVAILABLE_COLUMNS)
        invalid = ", ".join(invalid_columns)
        raise RuntimeError(f"Unsupported column(s): {invalid}. Available columns: {allowed}")

    return columns


def format_number(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"

    if isinstance(value, float):
        return f"{value:,.2f}"

    return f"{value:,}"


def build_rows(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    sorted_entries = sorted(
        entries,
        key=lambda entry: entry.get("volume") if isinstance(entry.get("volume"), (int, float)) else 0,
        reverse=True,
    )

    rows = []
    for entry in sorted_entries:
        address = str(entry.get("address", "")).strip()
        if not address:
            continue

        rank = len(rows) + 1
        rows.append(
            {
                "label": f"top #{rank}",
                "address": address,
                "description": (
                    f"HIP-3 leaderboard rank #{rank} by volume. "
                    f"Volume: {format_number(entry.get('volume'))}; "
                    f"Fees paid: {format_number(entry.get('fees_paid'))}; "
                    f"Deployer fees paid: {format_number(entry.get('deployer_fees_paid'))}; "
                    f"Trade count: {format_number(entry.get('trade_count'))}; "
                    f"Symbols traded: {format_number(entry.get('symbols_traded'))}."
                ),
            }
        )

    return rows


def write_csv(
    rows: list[dict[str, str]],
    output_path: Path,
    columns: list[str],
    include_header: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, extrasaction="ignore")
        if include_header:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    try:
        columns = parse_columns(args.columns)
        entries, total_traders = fetch_leaderboard(args.period, args.sort_by, args.limit, args.timeout)
        if len(entries) < args.limit:
            total_note = f" Total traders reported by API: {total_traders}." if total_traders else ""
            print(
                f"Warning: requested {args.limit} rows, API returned {len(entries)} rows."
                f"{total_note}",
                file=sys.stderr,
            )
        rows = build_rows(entries)
        if not args.dry_run:
            write_csv(rows, Path(args.output), columns, include_header=not args.no_header)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Fetched {len(rows)} rows; dry run did not write {args.output}")
    else:
        print(f"Exported {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
