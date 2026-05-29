#!/usr/bin/env python3
"""CLI: score_market_dataset.py - score dataset quality."""
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_manager.quality_score import QualityScore


def main() -> int:
    parser = argparse.ArgumentParser(description="Score market dataset quality")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    scorer = QualityScore()
    result = scorer.score(Path(args.csv), args.symbol, args.timeframe)
    print("Score: " + str(result.score) + " Grade: " + result.grade)
    for w in result.warnings:
        print("  WARN: " + w)
    for e in result.errors:
        print("  ERROR: " + e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
