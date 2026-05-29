#!/usr/bin/env python3
"""Analyze regime attribution from CSV.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_analytics.regime_attribution import analyze_regime_attribution


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    returns = []
    signals = []
    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "return" in row:
                returns.append(float(row["return"]))
            if "signal" in row:
                signals.append(row["signal"])

    result = analyze_regime_attribution(returns, signals=signals)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
