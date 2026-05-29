#!/usr/bin/env python3
"""CLI: restore_dataset_version.py - restore a dataset from backup."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.versioning import Versioning


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore dataset version")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--confirm-restore", action="store_true", default=False)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    if not args.confirm_restore:
        print("ERROR: Restore requires --confirm-restore")
        return 1
    versioning = Versioning(Path(args.version).parent.parent)
    versioning.restore(Path(args.dataset), Path(args.version), confirm=True)
    print("Restored " + args.dataset + " from " + args.version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
