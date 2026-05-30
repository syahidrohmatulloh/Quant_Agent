"""Export briefing in dashboard-friendly JSON format.

Writes local JSON only. No network.
"""

import json
from pathlib import Path
from typing import Any, Dict


def export_dashboard_json(briefing: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dashboard = {
        "name": briefing["name"],
        "generated_at": briefing["generated_at"],
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "headline": briefing["summary"]["headline"],
        "alert_count": len(briefing["alerts"]),
        "critical_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "CRITICAL"),
        "warning_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "WARNING"),
        "info_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "INFO"),
        "top_alerts": briefing["alerts"][:10],
        "summary": briefing["summary"],
        "source_status": {
            "experiment": "loaded" if briefing["sections"].get("signals") else "missing",
            "portfolio": "loaded" if briefing["sections"].get("portfolio") else "missing",
            "pnl": "loaded" if briefing["sections"].get("simulated_pnl") else "missing",
            "risk": "loaded" if briefing["sections"].get("risk") else "missing",
            "data_quality": "loaded" if briefing["sections"].get("data_quality") else "missing",
            "research": "loaded" if briefing["sections"].get("research_analytics") else "missing",
        },
        "warnings": briefing.get("warnings", []),
        "errors": briefing.get("errors", []),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
