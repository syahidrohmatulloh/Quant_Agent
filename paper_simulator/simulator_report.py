"""Generate Markdown and JSON reports for paper simulator.

Paper-only disclaimer included.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from paper_simulator.position_book import PositionBook
from paper_simulator.pnl_engine import PnlSnapshot
from paper_simulator.exposure import ExposureReport


def generate_report(
    config: Dict[str, Any],
    decisions: List[Dict[str, Any]],
    intents: List[Any],
    fills: List[Any],
    position_book: PositionBook,
    pnl: Optional[PnlSnapshot],
    exposure: Optional[ExposureReport],
    output_path: str,
) -> Dict[str, Any]:
    """Generate Markdown report and JSON summary."""
    generated_at = datetime.now(timezone.utc).isoformat()

    md_lines = [
        "# Paper Portfolio Simulator Report",
        "",
        "**Generated at:** " + generated_at,
        "",
        "> **PAPER-ONLY / DATA-ONLY.** This is a local paper simulation only. It is not financial advice and does not guarantee performance.",
        "> No live trading. No order submission.",
        "",
        "## Config Summary",
        "",
        "- **Name:** " + str(config.get("name", "N/A")),
        "- **Initial Cash:** " + str(config.get("initial_cash", "N/A")),
        "- **Base Currency:** " + str(config.get("base_currency", "N/A")),
        "- **Symbols:** " + str(len(config.get("symbols", []))),
        "",
        "## Simulated Portfolio Summary",
        "",
        "- **Decisions Processed:** " + str(len(decisions)),
        "- **Order Intents Generated:** " + str(len(intents)),
        "- **Simulated Fills:** " + str(len(fills)),
        "- **Active Positions:** " + str(len(position_book.all_positions())),
        "",
    ]

    md_lines.extend([
        "## Latest Decisions Processed",
        "",
    ])
    for d in decisions[-5:]:
        md_lines.append("- `" + str(d.get("decision_id", "")) + "` | " + d.get("symbol", "") + " | " + d.get("action", "") + " | " + d.get("reason", ""))
    md_lines.append("")

    md_lines.extend([
        "## Simulated Fills",
        "",
    ])
    for f in fills[-5:]:
        md_lines.append(
            "- `" + f.fill_id + "` | " + f.symbol + " | " + f.side + " | qty=" + str(f.quantity)
            + " | price=" + str(f.fill_price) + " | cost=" + str(f.total_cost)
        )
    md_lines.append("")

    md_lines.extend([
        "## Positions",
        "",
    ])
    for pos in position_book.all_positions():
        md_lines.append(
            "- " + pos.symbol + " (" + pos.timeframe + ") | " + pos.side + " | qty=" + str(pos.quantity)
            + " | avg=" + str(pos.average_price) + " | realized=" + str(pos.realized_pnl)
            + " | unrealized=" + str(pos.unrealized_pnl)
        )
    md_lines.append("")

    if pnl:
        md_lines.extend([
            "## PnL Summary (Simulated)",
            "",
            "- **Realized PnL:** " + str(pnl.realized_pnl),
            "- **Unrealized PnL:** " + str(pnl.unrealized_pnl),
            "- **Total PnL:** " + str(pnl.total_pnl),
            "- **Total Costs:** " + str(pnl.total_costs),
            "- **Equity:** " + str(pnl.equity),
            "- **Cash (Simulated):** " + str(pnl.cash_simulated),
            "- **Gross Exposure:** " + str(pnl.gross_exposure),
            "- **Net Exposure:** " + str(pnl.net_exposure),
            "",
        ])

    if exposure:
        md_lines.extend([
            "## Exposure Summary",
            "",
            "- **Gross Exposure:** " + str(exposure.gross_exposure),
            "- **Net Exposure:** " + str(exposure.net_exposure),
            "- **Long Exposure:** " + str(exposure.long_exposure),
            "- **Short Exposure:** " + str(exposure.short_exposure),
            "- **Max Concentration:** " + str(exposure.max_concentration) + " (" + exposure.max_concentration_symbol + ")",
            "",
        ])

    all_warnings = []
    if pnl:
        all_warnings.extend(pnl.warnings)
    if exposure:
        all_warnings.extend(exposure.warnings)
    if all_warnings:
        md_lines.extend([
            "## Risk Warnings",
            "",
        ])
        for w in all_warnings:
            md_lines.append("- " + w)
        md_lines.append("")

    costs = config.get("costs", {})
    md_lines.extend([
        "## Cost Model Assumptions",
        "",
        "- **Spread (pips):** " + str(costs.get("spread_pips", "N/A")),
        "- **Slippage (pips):** " + str(costs.get("slippage_pips", "N/A")),
        "- **Commission per million:** " + str(costs.get("commission_per_million", "N/A")),
        "- **Min Commission:** " + str(costs.get("min_commission", "N/A")),
        "",
        "> Disclaimer: This cost model is conservative and may not match any real broker exactly.",
        "",
        "## Explicit Disclaimer",
        "",
        "This is a local paper simulation only. It is not financial advice and does not guarantee performance.",
        "No live trading. No order submission.",
        "",
    ])

    md_text = chr(10).join(md_lines)

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(md_text)

    json_path = str(p.with_suffix(".json"))
    summary = {
        "generated_at": generated_at,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "config_name": config.get("name"),
        "decisions_count": len(decisions),
        "intents_count": len(intents),
        "fills_count": len(fills),
        "positions": [pos.to_dict() for pos in position_book.all_positions()],
        "pnl": pnl.to_dict() if pnl else None,
        "exposure": exposure.to_dict() if exposure else None,
        "warnings": all_warnings,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    return {"markdown_path": str(p), "json_path": json_path}
