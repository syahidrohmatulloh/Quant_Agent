#!/usr/bin/env python3
"""CLI: Validate briefing configuration.

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json

from briefing.briefing_config import load_config, validate_config


def main():
    parser = argparse.ArgumentParser(description="Validate briefing config")
    parser.add_argument("--config", required=True, help="Path to briefing config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing sources")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"FAIL: Could not load config: {e}")
        sys.exit(1)

    result = validate_config(config, allow_missing=args.allow_missing)

    print(f"Config name: {config.get('name', 'unknown')}")
    print(f"Valid: {result['valid']}")
    if result["errors"]:
        print("Errors:")
        for err in result["errors"]:
            print(f"  - {err}")
    if result["warnings"]:
        print("Warnings:")
        for warn in result["warnings"]:
            print(f"  - {warn}")

    if not result["valid"]:
        sys.exit(1)

    print("OK: Config is valid and safe.")
    sys.exit(0)


if __name__ == "__main__":
    main()
