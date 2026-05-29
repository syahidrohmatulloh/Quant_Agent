#!/usr/bin/env python3
"""CLI: Run the full daily paper workflow.
Paper-only. No live trading. No order submission.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from paper_orchestration.daily_runner import DailyRunner


def main():
    parser = argparse.ArgumentParser(description="Run daily paper workflow.")
    parser.add_argument("--config", required=True, help="Path to orchestration config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing experiment config/CSV")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    runner = DailyRunner(config_path=args.config, allow_missing_experiment=args.allow_missing)
    result = runner.run()
    print("\nWorkflow completed successfully.")
    print("Run ID:", result["run_id"])


if __name__ == "__main__":
    main()
