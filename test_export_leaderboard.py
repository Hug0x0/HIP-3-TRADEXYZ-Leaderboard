import csv
import json
import tempfile
import unittest
from pathlib import Path

import export_leaderboard as exporter


class ExportLeaderboardTests(unittest.TestCase):
    def test_parse_columns_rejects_unknown_columns(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Unsupported column"):
            exporter.parse_columns("label,address,bad")

    def test_build_rows_sorts_by_volume_and_applies_template(self) -> None:
        rows = exporter.build_rows(
            [
                {
                    "address": "0x0000000000000000000000000000000000000002",
                    "volume": 20,
                },
                {
                    "address": "0x0000000000000000000000000000000000000001",
                    "volume": 50,
                },
            ],
            label_template="TRADE.xyz #{rank}",
        )

        self.assertEqual(rows[0]["label"], "TRADE.xyz #1")
        self.assertEqual(rows[0]["address"], "0x0000000000000000000000000000000000000001")
        self.assertEqual(rows[1]["label"], "TRADE.xyz #2")

    def test_build_rows_respects_top_limit(self) -> None:
        rows = exporter.build_rows(
            [
                {
                    "address": "0x0000000000000000000000000000000000000001",
                    "volume": 10,
                },
                {
                    "address": "0x0000000000000000000000000000000000000002",
                    "volume": 5,
                },
            ],
            top=1,
        )

        self.assertEqual(len(rows), 1)

    def test_build_rows_skips_invalid_addresses(self) -> None:
        rows = exporter.build_rows(
            [
                {
                    "address": "not-an-address",
                    "volume": 100,
                },
                {
                    "address": "0x0000000000000000000000000000000000000001",
                    "volume": 50,
                },
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["address"], "0x0000000000000000000000000000000000000001")

    def test_write_csv_without_header(self) -> None:
        rows = [{"label": "top #1", "address": "0x0000000000000000000000000000000000000001"}]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "labels.csv"
            exporter.write_csv(rows, path, ["label", "address"], include_header=False)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(),
                "top #1,0x0000000000000000000000000000000000000001",
            )

    def test_write_csv_with_header(self) -> None:
        rows = [{"label": "top #1", "address": "0x0000000000000000000000000000000000000001"}]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "labels.csv"
            exporter.write_csv(rows, path, ["label", "address"], include_header=True)

            with path.open(newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                self.assertEqual(next(reader)["label"], "top #1")

    def test_write_json_filters_columns(self) -> None:
        rows = [
            {
                "label": "top #1",
                "address": "0x0000000000000000000000000000000000000001",
                "description": "hidden",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "labels.json"
            exporter.write_json(rows, path, ["label", "address"])

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                [
                    {
                        "label": "top #1",
                        "address": "0x0000000000000000000000000000000000000001",
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
