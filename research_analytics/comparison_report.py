"""Comparison report generation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def generate_comparison_report(
    config: Dict[str, Any],
    performance: Dict[str, Any],
    drawdown: Dict[str, Any],
    signal_quality: Dict[str, Any],
    regime_attribution: Dict[str, Any],
    strategy_attribution: Dict[str, Any],
    stability: Dict[str, Any],
    output_dir: str,
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    md_path = Path(output_dir) / "research_analytics_report.md"
    json_path = Path(output_dir) / "research_analytics_report.json"

    md_lines = [
        "# Research Analytics Report",
        "",
        f"Generated at: {ts}",
        "",
        "> **PAPER-ONLY / DATA-ONLY. No live trading. No order submission.**",
        "",
        "## Disclaimer",
        "This report is for research and paper trading only. It is not financial advice and does not guarantee performance.",
        "Historical simulation only. Past performance does not guarantee future results.",
        "",
        "## Config Summary",
        f"- Name: {config.get('name', 'N/A')}",
        f"- Paper only: {config.get('paper_only')}",
        f"- Data only: {config.get('data_only')}",
        f"- No order submission: {config.get('no_order_submission')}",
        "",
        "## Datasets",
    ]
    for ds in config.get("datasets", []):
        md_lines.append(f"- {ds.get('symbol')} {ds.get('timeframe')} ({ds.get('csv')})")
    md_lines.append("")

    md_lines.extend([
        "## Performance Metrics",
        "```json",
        json.dumps(performance, indent=2),
        "```",
        "",
        "## Drawdown Analysis",
        "```json",
        json.dumps(drawdown, indent=2),
        "```",
        "",
        "## Signal Quality",
        "```json",
        json.dumps(signal_quality, indent=2),
        "```",
        "",
        "## Regime Attribution",
        "```json",
        json.dumps(regime_attribution, indent=2),
        "```",
        "",
        "## Strategy Attribution",
        "```json",
        json.dumps(strategy_attribution, indent=2),
        "```",
        "",
        "## Stability Analysis",
        "```json",
        json.dumps(stability, indent=2),
        "```",
        "",
        "## Warnings / Errors",
    ])

    all_warnings = []
    all_errors = []
    for section in (performance, drawdown, signal_quality, regime_attribution, strategy_attribution, stability):
        if isinstance(section, dict):
            all_warnings.extend(section.get("warnings", []))
            all_errors.extend(section.get("errors", []))

    if all_warnings:
        for w in all_warnings:
            md_lines.append(f"- Warning: {w}")
    else:
        md_lines.append("- None")
    if all_errors:
        for e in all_errors:
            md_lines.append(f"- Error: {e}")
    else:
        md_lines.append("- None")

    md_lines.extend([
        "",
        "## Next Steps",
        "1. Review manually.",
        "2. Improve data quality if needed.",
        "3. Keep paper-only.",
    ])

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    report_payload = {
        "title": "Research Analytics Report",
        "generated_at": ts,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "config_summary": config,
        "performance": performance,
        "drawdown": drawdown,
        "signal_quality": signal_quality,
        "regime_attribution": regime_attribution,
        "strategy_attribution": strategy_attribution,
        "stability": stability,
        "warnings": all_warnings,
        "errors": all_errors,
    }
    json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    return {
        "markdown_path": str(md_path),
        "json_path": str(json_path),
    }
