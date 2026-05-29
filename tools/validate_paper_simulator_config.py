"""Validate paper simulator config.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_simulator.simulator_config import load_simulator_config, validate_simulator_config


def main():
    parser = argparse.ArgumentParser(description="Validate paper simulator config.")
    parser.add_argument("--config", required=True, help="Path to simulator config JSON.")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV paths.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    config, ok, errors, warnings = load_simulator_config(args.config)
    if not ok:
        print("Config validation FAILED:")
        for e in errors:
            print("  ERROR: " + e)
        for w in warnings:
            print("  WARN:  " + w)
        sys.exit(1)

    for w in warnings:
        print("  WARN:  " + w)
    print("Config validation OK: " + config.get("name", "unnamed"))


if __name__ == "__main__":
    main()
