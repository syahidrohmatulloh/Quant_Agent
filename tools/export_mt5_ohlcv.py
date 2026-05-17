#!/usr/bin/env python3
"""
CLI tool to export historical MT5 OHLCV bars for a date range.
Data-only. No order execution. No live trading.
"""
import argparse
import sys
import csv
import json
from datetime import datetime

sys.path.insert(0, ".")

from broker_integration.mt5.mt5_market_data import MT5MarketData
from broker_integration.mt5.mt5_errors import MT5Error

PAPER_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def main():
    parser = argparse.ArgumentParser(description="Export MT5 OHLCV historical bars")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., EURUSD)")
    parser.add_argument("--timeframe", default="H1", help="Timeframe: M1,M5,M15,M30,H1,H4,D1")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", required=True, help="Output file (.csv or .jsonl)")
    parser.add_argument("--timeout", type=int, default=60000, help="MT5 init timeout ms")
    args = parser.parse_args()

    print(PAPER_DISCLAIMER)
    print()

    date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
    date_to = datetime.strptime(args.date_to, "%Y-%m-%d")

    client = MT5MarketData(config={"timeout": args.timeout})
    try:
        client.initialize()
        bars = client.copy_rates_range(args.symbol, args.timeframe, date_from, date_to)
        print(f"Fetched {len(bars)} bars for {args.symbol} {args.timeframe} from {date_from.date()} to {date_to.date()}")

        if args.output.endswith(".csv"):
            with open(args.output, "w", newline="", encoding="utf-8") as f:
                if bars:
                    writer = csv.DictWriter(f, fieldnames=bars[0].keys())
                    writer.writeheader()
                    for b in bars:
                        row = dict(b)
                        row["timestamp"] = row["timestamp"].isoformat()
                        writer.writerow(row)
            print(f"Saved CSV to {args.output}")
        elif args.output.endswith(".jsonl"):
            with open(args.output, "w", encoding="utf-8") as f:
                for b in bars:
                    row = dict(b)
                    row["timestamp"] = row["timestamp"].isoformat()
                    f.write(json.dumps(row, default=str) + "\n")
            print(f"Saved JSONL to {args.output}")
        else:
            print("[ERROR] Output must end with .csv or .jsonl")
            sys.exit(1)
    except MT5Error as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
