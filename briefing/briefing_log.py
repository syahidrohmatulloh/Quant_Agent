"""Append-only JSONL briefing log.

No credentials. No env vars.
"""

import json
from pathlib import Path
from typing import Any, Dict


def append_briefing_log(briefing: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "briefing_id": f"{briefing['name']}_{briefing['generated_at']}",
        "generated_at": briefing["generated_at"],
        "headline": briefing["summary"]["headline"],
        "alert_count": len(briefing["alerts"]),
        "critical_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "CRITICAL"),
        "warning_count": sum(1 for a in briefing["alerts"] if a.get("severity") == "WARNING"),
        "source_status": {
            "experiment": "loaded" if briefing["sections"].get("signals") else "missing",
            "portfolio": "loaded" if briefing["sections"].get("portfolio") else "missing",
            "pnl": "loaded" if briefing["sections"].get("simulated_pnl") else "missing",
            "risk": "loaded" if briefing["sections"].get("risk") else "missing",
            "data_quality": "loaded" if briefing["sections"].get("data_quality") else "missing",
        },
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
