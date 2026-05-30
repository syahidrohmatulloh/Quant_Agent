"""Generate Markdown and JSON briefing reports.

Writes local files only. No network. No credentials.
"""

import json
from pathlib import Path
from typing import Any, Dict


def write_markdown_report(briefing: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    msg_cfg = briefing.get("message", {})
    timezone = msg_cfg.get("timezone", "UTC") if isinstance(msg_cfg, dict) else "UTC"
    tone = msg_cfg.get("tone", "professional") if isinstance(msg_cfg, dict) else "professional"

    lines = []
    lines.append(f"# Daily Briefing: {briefing['name']}")
    lines.append("")
    lines.append(f"**Generated at:** {briefing['generated_at']} ({briefing.get('timezone', timezone)})")
    lines.append("")
    lines.append("> **DISCLAIMER:** This briefing is for research and paper trading only. It is not financial advice and does not guarantee performance.")
    lines.append("")
    lines.append("> **SAFETY:** Paper-only / data-only. No live trading. No order submission.")
    lines.append("")

    # Headline
    lines.append(f"## Headline: {briefing['summary']['headline']}")
    lines.append("")

    # Top alerts
    lines.append("## Top Alerts")
    lines.append("")
    if briefing["alerts"]:
        for alert in briefing["alerts"][:10]:
            lines.append(f"- **[{alert['severity']}]** {alert['title']}: {alert['message']}")
    else:
        lines.append("No alerts.")
    lines.append("")

    # Signal summary
    lines.append("## Signal Summary")
    lines.append("")
    signals = briefing["sections"].get("signals", {})
    if signals:
        consensus = signals.get("consensus", "NEUTRAL")
        lines.append(f"- Consensus: **PAPER_{consensus}**")
        lines.append(f"- Strategy votes: {signals.get('strategy_votes', {})}")
    else:
        lines.append("No signal data available.")
    lines.append("")

    # Portfolio
    lines.append("## Paper Portfolio Summary")
    lines.append("")
    portfolio = briefing["sections"].get("portfolio", {})
    positions = portfolio.get("positions", []) if isinstance(portfolio, dict) else []
    lines.append(f"- Positions: {len(positions)}")
    if positions:
        for pos in positions[:5]:
            lines.append(f"  - {pos.get('symbol', '?')}: {pos.get('direction', '?')} {pos.get('size', 0)}")
    lines.append("")

    # Simulated PnL
    lines.append("## Simulated PnL Summary")
    lines.append("")
    pnl = briefing["sections"].get("simulated_pnl", {})
    lines.append(f"- Total simulated PnL: **{pnl.get('total_pnl', 0.0):.2f}**")
    lines.append(f"- Drawdown: {pnl.get('drawdown_pct', 0.0):.2%}")
    lines.append(f"- Costs: {pnl.get('total_costs', 0.0):.2f}")
    lines.append("")

    # Risk
    lines.append("## Exposure / Risk Summary")
    lines.append("")
    risk = briefing["sections"].get("risk", {})
    lines.append(f"- Gross exposure: {risk.get('gross_exposure', 0.0):.2%}")
    lines.append(f"- Short exposure: {risk.get('short_exposure', 0.0):.2%}")
    lines.append("")

    # Data quality
    lines.append("## Data Quality Summary")
    lines.append("")
    dq = briefing["sections"].get("data_quality", {})
    lines.append(f"- Catalog status: {dq.get('catalog_status', 'unknown')}")
    lines.append(f"- Quality score: {dq.get('quality_score', 'N/A')}")
    lines.append(f"- Dataset count: {dq.get('dataset_count', 0)}")
    lines.append("")

    # Research
    lines.append("## Research Analytics Summary")
    lines.append("")
    research = briefing["sections"].get("research_analytics", {})
    if research:
        for k, v in research.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("No research analytics data.")
    lines.append("")

    # Missing source warnings
    if briefing.get("warnings"):
        lines.append("## Missing Source Warnings")
        lines.append("")
        for w in briefing["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    # Next steps
    lines.append("## Next Steps")
    lines.append("")
    for step in briefing["sections"].get("next_steps", []):
        lines.append(f"- {step}")
    lines.append("")

    # Final disclaimer
    lines.append("---")
    lines.append("")
    lines.append("**This briefing is for research and paper trading only. It is not financial advice and does not guarantee performance.**")
    lines.append("")
    lines.append("**Do not place real trades based on this report.**")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_json_report(briefing: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)


def write_alert_summary(briefing: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "name": briefing["name"],
        "generated_at": briefing["generated_at"],
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "alert_count": len(briefing["alerts"]),
        "critical_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "CRITICAL"),
        "warning_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "WARNING"),
        "info_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "INFO"),
        "alerts": briefing["alerts"],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
