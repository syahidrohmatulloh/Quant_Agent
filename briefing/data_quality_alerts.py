"""Data quality alerts.

Alerts from data manager catalog and import logs.
"""

from typing import Any, Dict, List, Optional
from briefing.alert_rules import create_alert


def detect_data_quality_alerts(
    data_catalog: Optional[Dict[str, Any]],
    import_log: Optional[List[Dict[str, Any]]],
    config: Dict[str, Any],
    timezone_str: str = "UTC",
) -> List[Dict[str, Any]]:
    alerts = []
    rules = config.get("alert_rules", {})
    if not rules.get("alert_on_data_quality_warning", True):
        return alerts

    # Low quality score from catalog
    if data_catalog:
        quality_score = data_catalog.get("quality_score")
        if quality_score is not None and isinstance(quality_score, (int, float)):
            if quality_score < 0.7:
                alerts.append(create_alert(
                    severity="WARNING",
                    category="data_quality",
                    title="Low Data Quality Score",
                    message=f"Data quality score {quality_score:.2f} below 0.70 threshold.",
                    source="data_manager_catalog",
                    timezone_str=timezone_str,
                    extra={"quality_score": quality_score},
                ))

        # Missing datasets
        datasets = data_catalog.get("datasets", [])
        for ds in (datasets or []):
            if ds.get("status") == "missing":
                alerts.append(create_alert(
                    severity="CRITICAL",
                    category="data_quality",
                    title=f"Missing Dataset: {ds.get('name', 'unknown')}",
                    message=f"Dataset {ds.get('name', 'unknown')} is marked missing.",
                    source="data_manager_catalog",
                    timezone_str=timezone_str,
                    extra={"dataset": ds.get("name")},
                ))
            elif ds.get("status") == "stale":
                alerts.append(create_alert(
                    severity="WARNING",
                    category="data_quality",
                    title=f"Stale Dataset: {ds.get('name', 'unknown')}",
                    message=f"Dataset {ds.get('name', 'unknown')} is stale.",
                    source="data_manager_catalog",
                    timezone_str=timezone_str,
                    extra={"dataset": ds.get("name")},
                ))

    # Import log warnings
    if import_log:
        latest = import_log[-1] if import_log else {}
        if latest.get("status") == "warning":
            alerts.append(create_alert(
                severity="WARNING",
                category="data_quality",
                title="Import Warning",
                message=f"Latest import warning: {latest.get('message', 'unknown')}",
                source="data_manager_import_log",
                timezone_str=timezone_str,
                extra={"import_record": latest},
            ))
        elif latest.get("status") == "error":
            alerts.append(create_alert(
                severity="CRITICAL",
                category="data_quality",
                title="Import Error",
                message=f"Latest import error: {latest.get('message', 'unknown')}",
                source="data_manager_import_log",
                timezone_str=timezone_str,
                extra={"import_record": latest},
            ))

        # Low row count
        for rec in import_log[-5:]:
            row_count = rec.get("row_count")
            if isinstance(row_count, int) and row_count < 100:
                alerts.append(create_alert(
                    severity="WARNING",
                    category="data_quality",
                    title="Low Row Count",
                    message=f"Import {rec.get('dataset', 'unknown')} has only {row_count} rows.",
                    source="data_manager_import_log",
                    timezone_str=timezone_str,
                    extra={"row_count": row_count, "dataset": rec.get("dataset")},
                ))

    return alerts
