"""Dashboard JSON export for readiness gate.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .readiness_score import ReadinessScore


class DashboardExport:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}


def export_dashboard(
    score: ReadinessScore,
    critical_count: int,
    warning_count: int,
    audit_summary: Dict[str, Any],
    top_findings: list,
    recommendations: list,
    warnings: list,
    errors: list,
) -> DashboardExport:
    export = DashboardExport()
    now = datetime.now(timezone.utc).isoformat()
    export.data = {
        "name": "quant_agent_mvp_readiness_gate",
        "generated_at": now,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "readiness_score": score.score,
        "grade": score.grade,
        "readiness_status": score.status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "audit_summary": audit_summary,
        "top_findings": top_findings,
        "recommendations": recommendations,
        "warnings": warnings,
        "errors": errors,
    }
    return export


def write_dashboard_json(export: DashboardExport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export.data, f, indent=2)
