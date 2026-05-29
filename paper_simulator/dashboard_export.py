"""Dashboard JSON export for paper simulator.

Write: reports/dashboard/paper_simulator/latest.json
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from paper_simulator.position_book import PositionBook
from paper_simulator.pnl_engine import PnlSnapshot
from paper_simulator.exposure import ExposureReport


def export_dashboard_json(
    config: Dict[str, Any],
    position_book: PositionBook,
    fills: List[Any],
    pnl: Optional[PnlSnapshot],
    exposure: Optional[ExposureReport],
    warnings: List[str],
    errors: List[str],
    output_path: str,
) -> str:
    """Export dashboard-compatible JSON."""
    generated_at = datetime.now(timezone.utc).isoformat()

    portfolio = {
        "initial_cash": config.get("initial_cash", 100000.0),
        "base_currency": config.get("base_currency", "USD"),
        "equity": pnl.equity if pnl else config.get("initial_cash", 100000.0),
        "cash_simulated": pnl.cash_simulated if pnl else config.get("initial_cash", 100000.0),
        "total_pnl": pnl.total_pnl if pnl else 0.0,
        "total_costs": pnl.total_costs if pnl else 0.0,
    }

    data = {
        "name": config.get("name", "paper_simulator"),
        "generated_at": generated_at,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "portfolio": portfolio,
        "positions": [pos.to_dict() for pos in position_book.all_positions()],
        "latest_fills": [f.to_dict() for f in fills[-10:]],
        "pnl": pnl.to_dict() if pnl else None,
        "exposure": exposure.to_dict() if exposure else None,
        "warnings": warnings,
        "errors": errors,
    }

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    return str(p)
