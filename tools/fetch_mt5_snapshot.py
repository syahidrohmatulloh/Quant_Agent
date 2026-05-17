#!/usr/bin/env python3
"""
CLI tool to fetch latest bid/ask/last tick snapshot for one symbol.
Data-only. No order execution. No live trading.
"""
import argparse
import sys
import json

sys.path.insert(0, ".")

from broker_integration.mt5.mt5_market_data import MT5MarketData
from broker_integration.mt5.mt5_errors import MT5Error

PAPER_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def main():
    parser = argparse.ArgumentParser(description="Fetch MT5 tick snapshot")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., EURUSD)")
    parser.add_argument("--output", default=None, help="Output JSON file")
    parser.add_argument("--timeout", type=int, default=60000, help="MT5 init timeout ms")
    args = parser.parse_args()

    print(PAPER_DISCLAIMER)
    print()

    client = MT5MarketData(config={"timeout": args.timeout})
    try:
        client.initialize()
        tick = client.symbol_info_tick(args.symbol)
        tick["timestamp"] = tick["timestamp"].isoformat()
        print(json.dumps(tick, indent=2, default=str))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(tick, f, indent=2, default=str)
            print(f"Saved to {args.output}")
    except MT5Error as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
