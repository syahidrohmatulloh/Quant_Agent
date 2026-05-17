#!/usr/bin/env python3
"""
CLI: Compare strategy signals for a specific symbol from experiment config.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from experiment_manager.experiment_config import load_config, validate_experiment_config
from strategy_runtime.batch_runner import run_batch
from experiment_manager.strategy_comparison import build_comparison_table
from experiment_manager.consensus import compute_consensus


def main():
    parser = argparse.ArgumentParser(description="Compare strategy signals for a symbol.")
    parser.add_argument("--config", required=True, help="Path to experiment config JSON")
    parser.add_argument("--symbol", required=True, help="Symbol to compare")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV files")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    config = load_config(args.config)
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=args.allow_missing)
    if not is_valid:
        print("Config validation failed:")
        for e in errors:
            print("  - " + e)
        sys.exit(1)

    sym_entry = None
    for s in config.get("symbols", []):
        if s.get("symbol") == args.symbol:
            sym_entry = s
            break
    if sym_entry is None:
        print("Symbol '" + args.symbol + "' not found in config.")
        sys.exit(1)

    strategies = config.get("strategies", [])
    strategy_names = [s["name"] for s in strategies]
    strategy_params_map = {s["name"]: s.get("params", {}) for s in strategies}

    batch_result = run_batch(
        sym_entry["csv"], strategy_names,
        symbol=sym_entry["symbol"], timeframe=sym_entry["timeframe"],
        strategy_params_map=strategy_params_map,
        validate=False,
    )

    comparison = build_comparison_table(batch_result.get("individual_results", []))
    consensus_cfg = config.get("consensus", {})
    consensus = compute_consensus(
        comparison,
        method=consensus_cfg.get("method", "majority_vote"),
        minimum_agreement=consensus_cfg.get("minimum_agreement", 0.6),
    )

    print("\nSymbol: " + args.symbol + " (" + sym_entry["timeframe"] + ")")
    print("CSV: " + sym_entry["csv"])
    print("\nStrategy Comparison:")
    print("{:<25} {:<10} {:<8} {:<8} {:<12}".format("strategy", "signal", "score", "weight", "confidence"))
    print("-" * 70)
    for row in comparison:
        print("{:<25} {:<10} {:<8} {:<8} {:<12}".format(str(row["strategy"]), str(row["signal"]), str(row["score"]), str(row["weight"]), str(row["confidence"])))

    print("\nConsensus:")
    print("  Signal: " + consensus["consensus_signal"])
    print("  Agreement: " + str(consensus["agreement_ratio"]))
    print("  Confidence: " + consensus["confidence_label"])
    print("  Conflict: " + str(consensus["conflict_detected"]))
    print("  Explanation: " + consensus["explanation"])


if __name__ == "__main__":
    main()
