#!/usr/bin/env python3
"""
CLI: Generate daily paper-only decision report from experiment config.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from experiment_manager.experiment_config import load_config, validate_experiment_config
from experiment_manager.experiment_runner import run_experiment


def main():
    parser = argparse.ArgumentParser(description="Generate daily paper-only decision report.")
    parser.add_argument("--config", required=True, help="Path to experiment config JSON")
    parser.add_argument("--output", default="reports/experiments/daily_decision_report.md", help="Report output path")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV files")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    config = load_config(args.config)
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=args.allow_missing)
    if not is_valid:
        print("Config validation failed:")
        for e in errors:
            print("  - " + e)
        sys.exit(1)

    result = run_experiment(
        config=config,
        config_path=args.config,
        output_dir=str(Path(args.output).parent),
    )

    import shutil
    shutil.copy(result["markdown_path"], args.output)
    print("\nDaily decision report saved to: " + args.output)


if __name__ == "__main__":
    main()
