#!/usr/bin/env python3
"""
CLI: List experiment history.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from experiment_manager.experiment_log import list_experiment_history


def main():
    parser = argparse.ArgumentParser(description="List experiment history.")
    parser.add_argument("--history-dir", default="reports/experiments/history", help="History directory")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    records = list_experiment_history(args.history_dir)
    if not records:
        print("\nNo experiment history found.")
        return

    print("\n{:<10} {:<25} {:<8} {:<10} {:<20}".format("run_id", "experiment", "symbols", "strategies", "generated_at"))
    print("-" * 90)
    for r in records:
        print("{:<10} {:<25} {:<8} {:<10} {:<20}".format(r["run_id"], r["experiment_name"], str(r["symbol_count"]), str(r["strategy_count"]), r["generated_at"]))

    print("\nTotal experiments: " + str(len(records)))


if __name__ == "__main__":
    main()
