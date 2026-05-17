#!/usr/bin/env python3
"""
CLI: Run a single Phase 10 strategy on a CSV file and save paper-only signal log.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path

from strategy_runtime.csv_strategy_runner import run_strategy_on_csv
from strategy_runtime.signal_log import log_signal


def main():
    parser = argparse.ArgumentParser(description="Run strategy signal on CSV data.")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--symbol", default=None, help="Symbol override")
    parser.add_argument("--timeframe", default=None, help="Timeframe override")
    parser.add_argument("--params", default=None, help="JSON strategy params, e.g. {\"lookback\":20}")
    parser.add_argument("--output", default="reports/signals/latest_signal.json", help="Signal output path")
    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_strategy_on_csv(
        args.csv, args.strategy,
        symbol=args.symbol, timeframe=args.timeframe,
        strategy_params=params, validate=True,
    )

    if result.get("latest_signal"):
        log_signal(result["latest_signal"])
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result["latest_signal"], f, indent=2)
        print(f"Signal saved to {out}")
    else:
        print("No signal generated.")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
