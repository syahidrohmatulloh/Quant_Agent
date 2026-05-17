#!/usr/bin/env python3
"""
CLI: Full CSV workflow: validate -> signal -> optional backtest -> report -> signal log.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path

from market_data.csv_validator import validate_csv
from strategy_runtime.csv_strategy_runner import run_strategy_on_csv, run_backtest_on_csv
from strategy_runtime.signal_log import log_signal
from strategy_runtime.batch_runner import run_batch


def main():
    parser = argparse.ArgumentParser(description="Run full CSV strategy workflow.")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--symbol", default=None, help="Symbol override")
    parser.add_argument("--timeframe", default=None, help="Timeframe override")
    parser.add_argument("--strategies", required=True, help="Comma-separated strategy names")
    parser.add_argument("--backtest", action="store_true", help="Run backtest")
    parser.add_argument("--initial", type=float, default=100000.0, help="Initial balance for backtest")
    parser.add_argument("--output", default="reports/csv_workflow/report.md", help="Report output path")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    strategies = [s.strip() for s in args.strategies.split(",")]

    # 1. Validate
    validation = validate_csv(args.csv, symbol=args.symbol, timeframe=args.timeframe)
    if not validation["valid"]:
        print("Validation failed:")
        for e in validation["errors"]:
            print(f"  - {e}")
        return

    # 2. Run strategies
    batch_result = run_batch(
        args.csv, strategies,
        symbol=args.symbol, timeframe=args.timeframe, validate=False,
    )

    # 3. Optional backtest (run on first strategy)
    backtest_result = None
    if args.backtest and strategies:
        backtest_result = run_backtest_on_csv(
            args.csv, strategies[0],
            symbol=args.symbol, timeframe=args.timeframe,
            initial_balance=args.initial,
        )

    # 4. Log signals
    for sig in batch_result.get("signals", []):
        if sig:
            log_signal(sig)

    # 5. Generate report
    report = _build_report(args.csv, validation, batch_result, backtest_result, strategies)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {out}")

    # Also save JSON report
    json_out = out.with_suffix(".json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump({
            "csv_path": args.csv,
            "symbol": args.symbol or validation["inferred_symbol"],
            "timeframe": args.timeframe or validation["inferred_timeframe"],
            "validation": validation,
            "strategies": strategies,
            "signals": batch_result.get("signals"),
            "backtest": backtest_result.get("backtest") if backtest_result else None,
            "disclaimer": "PAPER-ONLY / DATA-ONLY. No live trading. No order submission.",
        }, f, indent=2)
    print(f"JSON report saved to {json_out}")


def _build_report(csv_path, validation, batch_result, backtest_result, strategies):
    lines = [
        "# CSV Strategy Workflow Report",
        "",
        "> **PAPER-ONLY / DATA-ONLY. No live trading. No order submission.**",
        "> **This report is for research and educational purposes only.**",
        "",
        "## Data Source",
        f"- CSV file: `{csv_path}`",
        f"- Symbol: {validation['inferred_symbol']}",
        f"- Timeframe: {validation['inferred_timeframe']}",
        f"- Source: {validation['inferred_source']}",
        f"- First timestamp: {validation['first_timestamp']}",
        f"- Last timestamp: {validation['last_timestamp']}",
        f"- Row count: {validation['row_count']}",
        "",
        "## Validation",
        f"- Valid: {validation['valid']}",
    ]
    if validation['errors']:
        lines.append("### Errors")
        for e in validation['errors']:
            lines.append(f"- {e}")
    if validation['warnings']:
        lines.append("### Warnings")
        for w in validation['warnings']:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Strategies")
    for s in strategies:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## Latest Signals")
    for sig in batch_result.get("signals", []):
        if sig:
            lines.append(f"- **{sig['strategy']}**: {sig['direction']} | weight={sig.get('weight')} | {sig['timestamp']}")
    lines.append("")
    if backtest_result and backtest_result.get("backtest"):
        bt = backtest_result["backtest"]
        lines.append("## Backtest (Historical Simulation)")
        lines.append(f"- Total return: {bt.get('total_return')}")
        lines.append(f"- Volatility: {bt.get('volatility')}")
        lines.append(f"- Max drawdown: {bt.get('max_drawdown')}")
        lines.append(f"- Hit rate: {bt.get('hit_rate')}")
        lines.append(f"- Total trades: {bt.get('total_trades')}")
        lines.append(f"- Number of bars: {len(bt.get('equity_curve', []))}")
        lines.append("")
        lines.append("> **WARNING:** Backtest is historical simulation only. Past performance does not guarantee future results.")
        lines.append("")
    if validation['warnings']:
        lines.append("## Next Steps")
        lines.append("- Data quality warnings detected. Review CSV before using signals.")
        lines.append("")
    lines.append("---")
    lines.append("Generated by Quant_Agent Phase 12 -- CSV Workflow")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
