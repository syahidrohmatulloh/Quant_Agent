#!/usr/bin/env python3
"""
CLI: Validate a market CSV file.
Exit non-zero if fatal validation errors exist.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import sys
import json

from market_data.csv_validator import validate_csv


def main():
    parser = argparse.ArgumentParser(description="Validate market CSV data.")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--symbol", default=None, help="Symbol override")
    parser.add_argument("--timeframe", default=None, help="Timeframe override")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    result = validate_csv(args.csv, symbol=args.symbol, timeframe=args.timeframe)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Valid: {result['valid']}")
        print(f"Rows: {result['row_count']}")
        print(f"Symbol: {result['inferred_symbol']} | Timeframe: {result['inferred_timeframe']} | Source: {result['inferred_source']}")
        print(f"First: {result['first_timestamp']} | Last: {result['last_timestamp']}")
        if result['errors']:
            print("Errors:")
            for e in result['errors']:
                print(f"  - {e}")
        if result['warnings']:
            print("Warnings:")
            for w in result['warnings']:
                print(f"  - {w}")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
