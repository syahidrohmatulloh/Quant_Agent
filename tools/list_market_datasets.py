#!/usr/bin/env python3
"""
CLI: List detected market datasets in a directory.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json

from market_data.dataset_catalog import scan_datasets, list_datasets_table


def main():
    parser = argparse.ArgumentParser(description="List market datasets.")
    parser.add_argument("--data-dir", default="data/market", help="Directory to scan")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    datasets = scan_datasets(args.data_dir)
    if args.json:
        print(json.dumps(datasets, indent=2))
    else:
        print(list_datasets_table(args.data_dir))


if __name__ == "__main__":
    main()
