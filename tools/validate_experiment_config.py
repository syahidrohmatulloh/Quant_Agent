#!/usr/bin/env python3
"""
CLI: Validate experiment config JSON.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from experiment_manager.experiment_config import load_config, validate_experiment_config


def main():
    parser = argparse.ArgumentParser(description="Validate experiment config JSON.")
    parser.add_argument("--config", required=True, help="Path to experiment config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV files (preview mode)")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    config = load_config(args.config)
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=args.allow_missing)

    print("\nConfig: " + args.config)
    print("Experiment name: " + config.get("name", "N/A"))
    print("Valid: " + str(is_valid))

    if errors:
        print("\nErrors:")
        for e in errors:
            print("  - " + e)
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print("  - " + w)

    if not is_valid:
        sys.exit(1)

    print("\nConfig validation passed.")


if __name__ == "__main__":
    main()
