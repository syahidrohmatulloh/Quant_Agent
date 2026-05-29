#!/usr/bin/env python3
"""CLI: list_dataset_versions.py - list backup versions for a dataset."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.versioning import Versioning


def main() -> int:
    parser = argparse.ArgumentParser(description="List dataset versions")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--backup-dir", required=True)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    versioning = Versioning(Path(args.backup_dir))
    versions = versioning.list_versions(Path(args.dataset))
    print("Versions for " + args.dataset + ": " + str(len(versions)))
    for v in versions:
        print("  " + v.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
