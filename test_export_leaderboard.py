import unittest

from export_leaderboard import build_rows


class BuildRowsTest(unittest.TestCase):
    def test_sorts_by_numeric_volume_and_skips_empty_addresses(self):
        rows = build_rows(
            [
                {"address": "0xlow", "volume": 10},
                {"address": "", "volume": 999},
                {"address": "0xhigh", "volume": 25},
                {"address": "0xmissing"},
            ]
        )

        self.assertEqual(
            rows,
            [
                {"label": "top #1", "address": "0xhigh"},
                {"label": "top #2", "address": "0xlow"},
                {"label": "top #3", "address": "0xmissing"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
