# HIP-3 Leaderboard

Export HIP-3 TRADE.xyz leaderboard addresses from the Loris API to CSV.

Default output:

```csv
label,address
top #1,0x...
top #2,0x...
```

Import-friendly output without a header:

```csv
top #1,0xc926ddba8b7617dbc65712f20cf8e1b58b8598d3
top #2,0x77001f3760e212769cb102dd82477e1b07f84216
```

## Usage

```bash
python3 export_leaderboard.py
```

By default, the script calls:

```text
https://loris.tools/api/hip3-analytics/leaderboard?period=all&sort_by=volume&limit=500
```

and writes both:

```text
hip3_leaderboard_labels.csv
exports/hip3_leaderboard_YYYY-MM-DD.csv
```

## Options

```bash
python3 export_leaderboard.py --period all --sort-by volume --limit 500 --output labels.csv
```

Write rows without a header:

```bash
python3 export_leaderboard.py --no-header
```

Choose columns:

```bash
python3 export_leaderboard.py --columns label,address
python3 export_leaderboard.py --columns label,address,description
```

Skip the dated export:

```bash
python3 export_leaderboard.py --no-dated-export
```

Test the API without writing files:

```bash
python3 export_leaderboard.py --dry-run
```

## API Limitation

The Loris endpoint reports the total number of traders, but currently returns only the first 100 leaderboard rows. If you request more than the API returns, the script prints a warning like:

```text
Warning: requested 500 rows, API returned 100 rows. Total traders reported by API: 277549.
```

Source API:

```text
https://loris.tools/api/hip3-analytics/leaderboard
```
