#!/usr/bin/env python3
"""Validate research analytics config.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_analytics.research_config import validate_research_config


def main():
    parser = argparse.ArgumentParser(description="Validate research analytics config")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing optional fields")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    ok, errors, warnings = validate_research_config(config, allow_missing=args.allow_missing)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if ok:
        print("OK: Config valid.")
        sys.exit(0)
    else:
        print("FAIL: Config invalid.")
        sys.exit(1)


if __name__ == "__main__":
    main()
