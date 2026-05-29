#!/usr/bin/env python3
"""CLI: import_market_csv.py - full import workflow from config."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.import_config import ImportConfig, ConfigValidationError
from data_manager.importer import Importer


def main() -> int:
    parser = argparse.ArgumentParser(description="Import market CSV from config")
    parser.add_argument("--config", required=True, help="Path to import config JSON")
    parser.add_argument("--allow-external-raw", action="store_true", default=False)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("No broker calls. No live network. No credential input prompts.")
    try:
        cfg = ImportConfig(Path(args.config), allow_external_raw=args.allow_external_raw)
        if not cfg.is_valid:
            print("Config validation failed:")
            for e in cfg.errors:
                print("  ERROR: " + e)
            return 1
        importer = Importer(cfg)
        result = importer.run()
        if result.errors:
            print("Import completed with errors:")
            for e in result.errors:
                print("  ERROR: " + e)
        else:
            print("Import completed successfully")
        for dr in result.dataset_results:
            print("  " + dr["symbol"] + " " + dr["timeframe"] + ": "
                  "in=" + str(dr["rows_in"]) + " out=" + str(dr["rows_out"]) + " "
                  "dropped=" + str(dr["rows_dropped"]) + " score=" + str(dr["quality_score"]) + " "
                  "grade=" + dr["grade"])
        return 0 if not result.errors else 1
    except ConfigValidationError as e:
        print("FAIL: " + str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
