#!/usr/bin/env python3
"""
CLI: Run full strategy experiment from config.
Saves Markdown + JSON + history log.
Paper-only. No live trading. No broker calls.
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
    parser = argparse.ArgumentParser(description="Run full strategy experiment from config.")
    parser.add_argument("--config", required=True, help="Path to experiment config JSON")
    parser.add_argument("--output-dir", default="reports/experiments", help="Output directory for reports")
    parser.add_argument("--dashboard-dir", default="reports/dashboard/experiments", help="Dashboard output directory")
    parser.add_argument("--history-dir", default="reports/experiments/history", help="History log directory")
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
    if warnings:
        print("Warnings:")
        for w in warnings:
            print("  - " + w)

    result = run_experiment(
        config=config,
        config_path=args.config,
        output_dir=args.output_dir,
        dashboard_dir=args.dashboard_dir,
        history_dir=args.history_dir,
    )

    print("\nExperiment run_id: " + result["run_id"])
    print("Markdown: " + result["markdown_path"])
    print("JSON: " + result["json_path"])
    print("Dashboard: " + result["dashboard_path"])


if __name__ == "__main__":
    main()
