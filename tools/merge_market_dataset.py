#!/usr/bin/env python3
"""CLI: merge_market_dataset.py - merge source CSV into target dataset."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.merger import Merger


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge market dataset")
    parser.add_argument("--source", required=True, help="Source CSV path")
    parser.add_argument("--target", required=True, help="Target CSV path")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--mode", default="upsert_by_timestamp",
                        choices=["replace", "append", "upsert_by_timestamp"])
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    merger = Merger()
    result = merger.merge(
        Path(args.source), Path(args.target), mode=args.mode,
        backup_before_write=True, preserve_existing_if_new_invalid=True,
    )
    print("Merged: existing=" + str(result.rows_existing) + " new=" + str(result.rows_new) + " "
          "out=" + str(result.rows_out) + " mode=" + result.mode)
    if result.backup_path:
        print("Backup: " + result.backup_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
