"""
Experiment runner: validates CSVs, runs strategies, computes consensus, saves reports.
Paper-only. No live trading. No broker calls. No network.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from market_data.csv_validator import validate_csv
from strategy_runtime.csv_strategy_runner import run_strategy_on_csv, run_backtest_on_csv
from strategy_runtime.batch_runner import run_batch
from experiment_manager.strategy_comparison import build_comparison_table
from experiment_manager.consensus import compute_consensus
from experiment_manager.decision_report import generate_markdown_report, generate_json_result
from experiment_manager.experiment_log import append_experiment_log
from experiment_manager.dashboard_export import export_dashboard_json


def run_experiment(config, config_path, output_dir="reports/experiments", dashboard_dir="reports/dashboard/experiments", history_dir="reports/experiments/history"):
    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    experiment_name = config.get("name", "unnamed_experiment")
    run_id = str(uuid.uuid4())[:8]
    generated_at = datetime.now(timezone.utc).isoformat()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dash_dir = Path(dashboard_dir)
    dash_dir.mkdir(parents=True, exist_ok=True)

    symbols = config.get("symbols", [])
    strategies = config.get("strategies", [])
    strategy_names = [s["name"] for s in strategies]
    strategy_params_map = {s["name"]: s.get("params", {}) for s in strategies}
    do_backtest = config.get("backtest", False)
    consensus_cfg = config.get("consensus", {})
    consensus_method = consensus_cfg.get("method", "majority_vote")
    minimum_agreement = consensus_cfg.get("minimum_agreement", 0.6)
    risk_notes = config.get("risk_notes", {})

    symbol_results = []
    all_errors = []
    all_warnings = []

    for sym_entry in symbols:
        sym = sym_entry["symbol"]
        tf = sym_entry["timeframe"]
        csv_path = sym_entry["csv"]

        validation = validate_csv(csv_path, symbol=sym, timeframe=tf)
        if not validation["valid"]:
            all_errors.extend(["[" + sym + "] " + e for e in validation["errors"]])
        all_warnings.extend(["[" + sym + "] " + w for w in validation["warnings"]])

        batch_result = run_batch(
            csv_path, strategy_names,
            symbol=sym, timeframe=tf,
            strategy_params_map=strategy_params_map,
            validate=False,
        )

        individual_results = batch_result.get("individual_results", [])

        backtest_results = []
        if do_backtest:
            for strat_name in strategy_names:
                bt = run_backtest_on_csv(
                    csv_path, strat_name,
                    symbol=sym, timeframe=tf,
                    strategy_params=strategy_params_map.get(strat_name, {}),
                )
                backtest_results.append(bt)

        comparison = build_comparison_table(individual_results, backtest_results)
        consensus = compute_consensus(comparison, method=consensus_method, minimum_agreement=minimum_agreement)

        symbol_results.append({
            "symbol": sym,
            "timeframe": tf,
            "csv": csv_path,
            "validation": validation,
            "comparison": comparison,
            "consensus": consensus,
        })

    validation_summary = {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
    }

    md_path = out_dir / (experiment_name + "_" + run_id + ".md")
    json_path = out_dir / (experiment_name + "_" + run_id + ".json")
    dashboard_path = dash_dir / "latest.json"

    generate_markdown_report(
        experiment_name, config, symbol_results, validation_summary,
        risk_notes=risk_notes, output_path=str(md_path),
    )
    generate_json_result(
        experiment_name, config, symbol_results, validation_summary,
        output_path=str(json_path),
    )
    export_dashboard_json(
        experiment_name, symbol_results, output_path=str(dashboard_path),
    )

    history_file = append_experiment_log(
        history_dir=history_dir,
        run_id=run_id,
        experiment_name=experiment_name,
        config_path=config_path,
        symbol_count=len(symbols),
        strategy_count=len(strategies),
        result_path=str(json_path),
        dashboard_json_path=str(dashboard_path),
    )

    print("\nExperiment complete: " + experiment_name)
    print("  Markdown report: " + str(md_path))
    print("  JSON result: " + str(json_path))
    print("  Dashboard JSON: " + str(dashboard_path))
    print("  History log: " + history_file)
    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    return {
        "run_id": run_id,
        "experiment_name": experiment_name,
        "generated_at": generated_at,
        "paper_only": True,
        "data_only": True,
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "dashboard_path": str(dashboard_path),
        "history_file": history_file,
        "symbol_results": symbol_results,
        "validation_summary": validation_summary,
    }
