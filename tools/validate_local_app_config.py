#!/usr/bin/env python3
"""CLI: Validate local app configuration.

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json

from local_app.app_config import load_config, validate_config
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Validate local app config")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing config files")
    parser.add_argument("--allow-nonlocal-host", action="store_true", help="Allow dashboard host 0.0.0.0")
    args = parser.parse_args()

    print_disclaimer()
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

    result = validate_config(
        config,
        allow_missing=args.allow_missing,
        allow_nonlocal_host=args.allow_nonlocal_host,
    )

    print(f"Config name: {config.get('name', 'unknown')}")
    print(f"Valid: {result['valid']}")
    if result["errors"]:
        print("Errors:")
        for err in result["errors"]:
            print(f" - {err}")
    if result["warnings"]:
        print("Warnings:")
        for warn in result["warnings"]:
            print(f" - {warn}")

    if not result["valid"]:
        sys.exit(1)

    print("OK: Config is valid and safe.")
    sys.exit(0)


if __name__ == "__main__":
    main()
