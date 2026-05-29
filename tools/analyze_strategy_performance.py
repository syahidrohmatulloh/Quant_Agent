#!/usr/bin/env python3
"""Analyze strategy performance from CSV.

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

from research_analytics.performance_metrics import compute_performance_metrics
from research_analytics.drawdown_analysis import analyze_drawdown


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

    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))

    perf = compute_performance_metrics(returns, equity=equity, signals=signals)
    dd = analyze_drawdown(equity)
    out = {"performance": perf, "drawdown": dd}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
