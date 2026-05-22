# HIP-3 Leaderboard

Export HIP-3 leaderboard addresses from the Loris API to a CSV with this format:

```csv
label,address
top #1,0x...
top #2,0x...
```

## Usage

```bash
python3 export_leaderboard.py
```

By default, the script calls:

```text
https://loris.tools/api/hip3-analytics/leaderboard?period=all&sort_by=volume&limit=500
```

and writes:

```text
hip3_leaderboard_labels.csv
```

## Options

```bash
python3 export_leaderboard.py --period all --sort-by volume --limit 500 --output labels.csv
```
