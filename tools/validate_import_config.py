#!/usr/bin/env python3
"""CLI: validate_import_config.py - validates an import config JSON."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.import_config import ImportConfig, ConfigValidationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate import config JSON")
    parser.add_argument("--config", required=True, help="Path to import config JSON")
    parser.add_argument("--allow-missing", action="store_true", default=False)
    parser.add_argument("--allow-external-raw", action="store_true", default=False)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    try:
        cfg = ImportConfig(
            Path(args.config),
            allow_missing=args.allow_missing,
            allow_external_raw=args.allow_external_raw,
        )
        if cfg.is_valid:
            print("OK: config is valid")
            return 0
        else:
            print("FAIL: config has errors")
            for e in cfg.errors:
                print("  ERROR: " + e)
            for w in cfg.warnings:
                print("  WARN: " + w)
            return 1
    except ConfigValidationError as e:
        print("FAIL: " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
