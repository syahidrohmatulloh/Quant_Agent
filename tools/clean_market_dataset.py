#!/usr/bin/env python3
"""CLI: clean_market_dataset.py - clean a market dataset CSV."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.cleaner import Cleaner


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean market dataset CSV")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--source-name", required=True)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    cleaner = Cleaner()
    result = cleaner.clean(Path(args.csv), output_path=Path(args.output))
    print("Cleaned: in=" + str(result.rows_in) + " out=" + str(result.rows_out) + " "
          "dropped=" + str(result.rows_dropped) + " duplicates=" + str(result.duplicate_count) + " "
          "malformed=" + str(result.malformed_count) + " anomalies=" + str(result.price_anomaly_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
