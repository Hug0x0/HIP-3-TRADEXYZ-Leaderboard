#!/usr/bin/env python3
"""Export HIP-3 leaderboard addresses to a label/address/description CSV."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export HIP-3 leaderboard addresses as label,address,description."
    )
    parser.add_argument("--period", default="all", help="API period parameter.")
    parser.add_argument("--sort-by", default="volume", help="API sort_by parameter.")
    parser.add_argument("--limit", type=int, default=500, help="Number of rows to request.")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"CSV output path. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def fetch_leaderboard(period: str, sort_by: str, limit: int) -> list[dict[str, Any]]:
    query = urlencode({"period": period, "sort_by": sort_by, "limit": limit})
    request = Request(
        f"{API_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "hip3-leaderboard-exporter/1.0",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
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

    return [row for row in data if isinstance(row, dict)]


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
    for rank, entry in enumerate(sorted_entries, start=1):
        address = str(entry.get("address", "")).strip()
        if not address:
            continue

        description = (
            f"HIP-3 leaderboard rank #{rank} by volume. "
            f"Volume: {format_number(entry.get('volume'))}; "
            f"Fees paid: {format_number(entry.get('fees_paid'))}; "
            f"Deployer fees paid: {format_number(entry.get('deployer_fees_paid'))}; "
            f"Trade count: {format_number(entry.get('trade_count'))}; "
            f"Symbols traded: {format_number(entry.get('symbols_traded'))}."
        )
        rows.append(
            {
                "label": f"top #{rank}",
                "address": address,
                "description": description,
            }
        )

    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["label", "address", "description"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    try:
        entries = fetch_leaderboard(args.period, args.sort_by, args.limit)
        rows = build_rows(entries)
        write_csv(rows, Path(args.output))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
