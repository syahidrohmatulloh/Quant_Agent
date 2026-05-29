#!/usr/bin/env python3
"""Run full research analytics pipeline.

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

from research_analytics.research_config import load_research_config
from research_analytics.performance_metrics import compute_performance_metrics
from research_analytics.drawdown_analysis import analyze_drawdown
from research_analytics.signal_quality import analyze_signal_quality
from research_analytics.regime_attribution import analyze_regime_attribution
from research_analytics.stability_analysis import analyze_stability
from research_analytics.comparison_report import generate_comparison_report
from research_analytics.analytics_export import export_dashboard_json


def load_csv_returns(path: str):
    returns = []
    signals = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "return" in row:
                returns.append(float(row["return"]))
            if "signal" in row:
                signals.append(row["signal"])
    return returns, signals


def main():
    parser = argparse.ArgumentParser(description="Run research analytics")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    config, ok, errors, warnings = load_research_config(args.config)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if not ok:
        print("FAIL: Config invalid.")
        sys.exit(1)

    # Load first dataset for demo
    ds = config["datasets"][0]
    returns, signals = load_csv_returns(ds["csv"])

    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))

    perf = compute_performance_metrics(returns, equity=equity, signals=signals, frequency="hourly")
    dd = analyze_drawdown(equity)
    sq = analyze_signal_quality(signals, returns=returns, forward_periods=1)
    ra = analyze_regime_attribution(returns, signals=signals)
    st = analyze_stability(returns, signals=signals)

    # Strategy attribution placeholder
    sa = {
        "contribution_by_strategy": {},
        "contribution_by_symbol": {},
        "contribution_by_timeframe": {},
        "consensus_vs_individual": {},
        "agreement_ratio": None,
        "conflict_ratio": None,
        "best_strategy_historical": None,
        "worst_strategy_historical": None,
        "warnings": [],
        "note": "No ranking implies future performance. Historical simulation only.",
    }

    out_dir = config.get("output_dir", "reports/research_analytics")
    report_paths = generate_comparison_report(
        config, perf, dd, sq, ra, sa, st, out_dir
    )
    print(f"Report written: {report_paths['markdown_path']}")
    print(f"JSON written: {report_paths['json_path']}")

    dash_out = config.get("dashboard_output", "reports/dashboard/research_analytics/latest.json")
    export_dashboard_json(config, perf, dd, sq, ra, sa, st, dash_out)
    print(f"Dashboard JSON written: {dash_out}")


if __name__ == "__main__":
    main()
