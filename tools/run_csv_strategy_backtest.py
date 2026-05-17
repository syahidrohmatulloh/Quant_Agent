#!/usr/bin/env python3
"""
CLI: Run historical simulation (backtest) on CSV data.
Paper-only. No profitability guarantee.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path

from strategy_runtime.csv_strategy_runner import run_backtest_on_csv


def main():
    parser = argparse.ArgumentParser(description="Run backtest on CSV data.")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--symbol", default=None, help="Symbol override")
    parser.add_argument("--timeframe", default=None, help="Timeframe override")
    parser.add_argument("--initial", type=float, default=100000.0, help="Initial balance")
    parser.add_argument("--params", default=None, help='JSON strategy params')
    parser.add_argument("--output", default="reports/csv_workflow/backtest_result.json", help="Output JSON path")
    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_backtest_on_csv(
        args.csv, args.strategy,
        symbol=args.symbol, timeframe=args.timeframe,
        initial_balance=args.initial, strategy_params=params,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Backtest result saved to {out}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
