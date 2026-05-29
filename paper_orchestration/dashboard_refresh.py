"""
Refresh dashboard JSON with paper orchestration summary.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def refresh_dashboard(
    run_id: str,
    portfolio_summary: Dict[str, Any],
    latest_decisions: List[Dict[str, Any]],
    risk_warnings: List[str],
    audit_status: str,
    output_path: str,
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    dashboard = {
        "run_id": run_id,
        "generated_at": generated_at,
        "portfolio_summary": portfolio_summary,
        "latest_decisions": latest_decisions,
        "risk_warnings": risk_warnings,
        "audit_status": audit_status,
        "paper_only": True,
        "no_order_submission": True,
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, default=str)
    return str(out)
