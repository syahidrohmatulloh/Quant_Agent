"""Alert rule definitions and base alert structure.

All alerts are paper-only and data-only.
No order submission implied.
"""

from typing import Any, Dict, List
from datetime import datetime, timezone


SEVERITIES = ["INFO", "WARNING", "CRITICAL"]
CATEGORIES = ["signal", "risk", "pnl", "data_quality", "missing_source", "system"]


def create_alert(
    severity: str,
    category: str,
    title: str,
    message: str,
    source: str,
    timezone_str: str = "UTC",
    extra: Dict[str, Any] = None,
) -> Dict[str, Any]:
    if severity not in SEVERITIES:
        severity = "INFO"
    if category not in CATEGORIES:
        category = "system"
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "message": message,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timezone": timezone_str,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "extra": extra or {},
    }


def filter_alerts(alerts: List[Dict[str, Any]], max_alerts: int = 20) -> List[Dict[str, Any]]:
    # Sort by severity: CRITICAL first, then WARNING, then INFO
    severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    sorted_alerts = sorted(alerts, key=lambda a: severity_order.get(a.get("severity", "INFO"), 3))
    return sorted_alerts[:max_alerts]
