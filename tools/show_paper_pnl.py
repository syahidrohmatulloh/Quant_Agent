"""Show paper PnL from log file.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Show paper PnL log.")
    parser.add_argument("--pnl", required=True, help="Path to PnL JSONL.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    records = []
    with open(args.pnl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("No PnL records found.")
        return

    latest = records[-1]
    print("Latest PnL snapshot: " + latest.get("timestamp", "unknown"))
    print("  Realized PnL:   " + str(latest.get("realized_pnl", 0)))
    print("  Unrealized PnL: " + str(latest.get("unrealized_pnl", 0)))
    print("  Total PnL:      " + str(latest.get("total_pnl", 0)))
    print("  Equity:         " + str(latest.get("equity", 0)))
    print("  Cash:           " + str(latest.get("cash_simulated", 0)))
    print("  Gross Exposure: " + str(latest.get("gross_exposure", 0)))
    print("  Net Exposure:   " + str(latest.get("net_exposure", 0)))
    print("  Records total:  " + str(len(records)))


if __name__ == "__main__":
    main()
