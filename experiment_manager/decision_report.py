"""
Markdown and JSON decision report generator.
Paper-only. No live trading. Not financial advice.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


def generate_markdown_report(experiment_name, config, symbol_results, validation_summary, risk_notes=None, output_path=None):
    generated_at = datetime.now(timezone.utc).isoformat()

    lines = []
    lines.append("# Daily Paper Decision Report: " + experiment_name)
    lines.append("")
    lines.append("**Generated at:** " + generated_at)
    lines.append("")
    lines.append("> **PAPER-ONLY / DATA-ONLY. No live trading. No order submission.**")
    lines.append("> **This report is for research and paper trading only. It is not financial advice and does not guarantee performance.**")
    lines.append("")
    lines.append("## Experiment Summary")
    lines.append("- **Name:** " + str(experiment_name))
    lines.append("- **Symbols:** " + str(len(config.get("symbols", []))))
    lines.append("- **Strategies:** " + str(len(config.get("strategies", []))))
    lines.append("- **Backtest enabled:** " + str(config.get("backtest", False)))
    lines.append("")
    lines.append("## Dataset Summary")

    for sym_res in symbol_results:
        sym = sym_res.get("symbol", "UNKNOWN")
        tf = sym_res.get("timeframe", "UNKNOWN")
        csv_path = sym_res.get("csv", "N/A")
        val = sym_res.get("validation", {})
        lines.append("- **" + sym + "** (" + tf + ") — `" + csv_path + "`")
        lines.append("  - Valid: " + str(val.get("valid", False)))
        lines.append("  - Rows: " + str(val.get("row_count", 0)))
        if val.get("warnings"):
            lines.append("  - Warnings: " + str(len(val.get("warnings", []))))

    lines.append("")
    lines.append("## Validation Warnings / Errors")
    has_issues = False
    for sym_res in symbol_results:
        val = sym_res.get("validation", {})
        if val.get("errors"):
            has_issues = True
            for e in val["errors"]:
                lines.append("- **ERROR** [" + str(sym_res.get("symbol")) + "]: " + str(e))
        if val.get("warnings"):
            has_issues = True
            for w in val["warnings"]:
                lines.append("- **WARNING** [" + str(sym_res.get("symbol")) + "]: " + str(w))
    if not has_issues:
        lines.append("- No validation issues detected.")

    lines.append("")
    lines.append("## Per-Symbol Strategy Comparison")
    for sym_res in symbol_results:
        sym = sym_res.get("symbol", "UNKNOWN")
        tf = sym_res.get("timeframe", "UNKNOWN")
        lines.append("")
        lines.append("### " + sym + " (" + tf + ")")
        lines.append("")
        lines.append("| strategy | signal | score | weight | confidence | backtest_return | max_drawdown | warnings |")
        lines.append("|----------|--------|-------|--------|------------|-----------------|--------------|----------|")
        for row in sym_res.get("comparison", []):
            warnings_str = "; ".join(row.get("warnings", [])) or "-"
            lines.append(
                "| " + str(row.get("strategy")) + " | " + str(row.get("signal")) + " | " + str(row.get("score")) + " | "
                + str(row.get("weight")) + " | " + str(row.get("confidence")) + " | " + str(row.get("backtest_return")) + " | "
                + str(row.get("max_drawdown")) + " | " + warnings_str + " |"
            )

    lines.append("")
    lines.append("## Consensus Summary")
    for sym_res in symbol_results:
        sym = sym_res.get("symbol", "UNKNOWN")
        con = sym_res.get("consensus", {})
        lines.append("")
        lines.append("### " + sym)
        lines.append("- **Consensus signal:** " + str(con.get("consensus_signal", "NEUTRAL")))
        lines.append("- **Agreement ratio:** " + str(con.get("agreement_ratio", 0)))
        lines.append("- **Confidence:** " + str(con.get("confidence_label", "none")))
        lines.append("- **Strategies:** " + str(con.get("strategy_count", 0)) + " (LONG=" + str(con.get("long_count", 0)) + ", SHORT=" + str(con.get("short_count", 0)) + ", NEUTRAL=" + str(con.get("neutral_count", 0)) + ")")
        lines.append("- **Conflict detected:** " + str(con.get("conflict_detected", False)))
        lines.append("- **Explanation:** " + str(con.get("explanation", "")))

    lines.append("")
    lines.append("## Risk Notes")
    if risk_notes:
        for k, v in risk_notes.items():
            lines.append("- **" + str(k) + ":** " + str(v))
    else:
        lines.append("- No specific risk notes configured.")
    lines.append("- **paper_only:** true")
    lines.append("- **data_only:** true")

    lines.append("")
    lines.append("## Next Action")
    lines.append("- **Review manually** — All signals are paper-only watchlist signals.")
    lines.append("- **Paper-only watchlist** — No live order submitted.")
    lines.append("- **No live order submitted** — This is a research signal only.")

    lines.append("")
    lines.append("---")
    lines.append("**Disclaimer:** This report is for research and paper trading only. It is not financial advice and does not guarantee performance. Past performance does not predict future results.")
    lines.append("")
    lines.append("Generated by Quant_Agent Phase 13 — Strategy Experiment Manager")

    report = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(report)

    return report


def generate_json_result(experiment_name, config, symbol_results, validation_summary, output_path=None):
    generated_at = datetime.now(timezone.utc).isoformat()
    result = {
        "experiment_name": experiment_name,
        "generated_at": generated_at,
        "paper_only": True,
        "data_only": True,
        "symbols": symbol_results,
        "warnings": validation_summary.get("warnings", []),
        "errors": validation_summary.get("errors", []),
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)

    return result
