#!/usr/bin/env python3
"""CLI: validate readiness gate config.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from readiness_gate.readiness_config import load_readiness_config, validate_readiness_config


def main():
    parser = argparse.ArgumentParser(description="Validate readiness gate configuration")
    parser.add_argument("--config", required=True, help="Path to readiness config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing optional configs")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config not found: {config_path}")
        sys.exit(1)

    config = load_readiness_config(config_path)
    messages = validate_readiness_config(config, allow_missing=args.allow_missing)

    if messages:
        for m in messages:
            print(f"ISSUE: {m}")
        sys.exit(1)
    else:
        print("OK: Readiness config is valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
