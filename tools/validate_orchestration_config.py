#!/usr/bin/env python3
"""CLI: Validate paper orchestration config.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from paper_orchestration.orchestration_config import load_orchestration_config, validate_orchestration_config


def main():
    parser = argparse.ArgumentParser(description="Validate paper orchestration config.")
    parser.add_argument("--config", required=True, help="Path to orchestration config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing experiment config")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    config = load_orchestration_config(args.config)
    is_valid, errors, warnings = validate_orchestration_config(config, allow_missing_experiment=args.allow_missing)

    if is_valid:
        print("Config is VALID.")
    else:
        print("Config is INVALID.")
    if errors:
        print("Errors:")
        for e in errors:
            print(" - " + e)
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(" - " + w)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
