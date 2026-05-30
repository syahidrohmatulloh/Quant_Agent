"""Builds the daily briefing object from all sources and alerts.

Paper-only / data-only. No order submission.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from briefing.source_loader import normalize_sources
from briefing.alert_rules import filter_alerts
from briefing.signal_alerts import detect_signal_alerts
from briefing.risk_alerts import detect_risk_alerts
from briefing.data_quality_alerts import detect_data_quality_alerts
from briefing.pnl_alerts import detect_pnl_alerts


def build_briefing(
    config: Dict[str, Any],
    loaded_sources: Dict[str, Any],
    previous_signals: Optional[Dict[str, Any]] = None,
    project_root: Optional[Any] = None,
) -> Dict[str, Any]:
    normalized = normalize_sources(loaded_sources)
    timezone_str = config.get("message", {}).get("timezone", "UTC")
    rules = config.get("alert_rules", {})

    alerts = []

    # Signal alerts
    alerts.extend(detect_signal_alerts(
        normalized.get("latest_experiment_summary"),
        previous_signals,
        config,
        timezone_str,
    ))

    # Risk alerts
    alerts.extend(detect_risk_alerts(
        normalized.get("paper_simulator_state"),
        normalized.get("latest_paper_orchestration_summary"),
        config,
        timezone_str,
    ))

    # Data quality alerts
    alerts.extend(detect_data_quality_alerts(
        normalized.get("data_manager_catalog"),
        normalized.get("data_manager_import_log"),
        config,
        timezone_str,
    ))

    # PnL alerts
    alerts.extend(detect_pnl_alerts(
        normalized.get("paper_simulator_pnl_records"),
        normalized.get("paper_simulator_state"),
        config,
        timezone_str,
    ))

    # Missing source alerts
    if rules.get("alert_on_missing_sources", True):
        for warning in loaded_sources.get("warnings", []):
            if "Missing source" in warning or "missing" in warning.lower():
                alerts.append({
                    "severity": "WARNING",
                    "category": "missing_source",
                    "title": "Missing Source",
                    "message": warning,
                    "source": "source_loader",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "timezone": timezone_str,
                    "paper_only": True,
                    "data_only": True,
                    "no_order_submission": True,
                })

    max_alerts = rules.get("max_alerts_per_briefing", 20)
    alerts = filter_alerts(alerts, max_alerts)

    # Counts
    critical_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
    warning_count = sum(1 for a in alerts if a.get("severity") == "WARNING")
    info_count = sum(1 for a in alerts if a.get("severity") == "INFO")

    # Build summaries
    experiment = normalized.get("latest_experiment_summary", {}) or {}
    orchestration = normalized.get("latest_paper_orchestration_summary", {}) or {}
    simulator = normalized.get("paper_simulator_state", {}) or {}
    research = normalized.get("latest_research_analytics_summary", {}) or {}
    catalog = normalized.get("data_manager_catalog", {}) or {}

    # Determine headline
    if critical_count > 0:
        headline = f"CRITICAL: {critical_count} critical alert(s) require attention."
    elif warning_count > 0:
        headline = f"WARNING: {warning_count} warning(s) detected."
    else:
        headline = "All systems nominal. No critical warnings."

    # Simulated PnL status
    total_pnl = simulator.get("total_pnl", 0.0)
    pnl_status = f"Simulated PnL: {total_pnl:.2f}"

    # Risk status
    gross_exposure = simulator.get("exposure", {}).get("gross_exposure", 0.0)
    risk_status = f"Gross exposure: {gross_exposure:.2%}"

    # Market data status
    catalog_status = catalog.get("status", "unknown")
    market_data_status = f"Data catalog status: {catalog_status}"

    # Experiment status
    experiment_status = experiment.get("status", "unknown")

    # Portfolio status
    portfolio = simulator.get("portfolio", {})
    positions = portfolio.get("positions", [])
    portfolio_status = f"{len(positions)} paper position(s)"

    # Next steps
    next_steps = [
        "Review daily briefing manually.",
        "Keep paper-only mode active.",
        "Improve data quality if warnings exist.",
        "Do not place real trades based on this report.",
    ]

    briefing = {
        "name": config.get("name", "daily_briefing"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timezone": timezone_str,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "summary": {
            "headline": headline,
            "market_data_status": market_data_status,
            "experiment_status": experiment_status,
            "paper_portfolio_status": portfolio_status,
            "simulated_pnl_status": pnl_status,
            "risk_status": risk_status,
            "alert_count": len(alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
        },
        "alerts": alerts,
        "sections": {
            "signals": experiment.get("signals", {}),
            "portfolio": portfolio,
            "simulated_pnl": {
                "total_pnl": total_pnl,
                "drawdown_pct": simulator.get("drawdown_pct", 0.0),
                "total_costs": simulator.get("total_costs", 0.0),
            },
            "risk": simulator.get("exposure", {}),
            "data_quality": {
                "catalog_status": catalog_status,
                "quality_score": catalog.get("quality_score"),
                "dataset_count": len(catalog.get("datasets", [])),
            },
            "research_analytics": research.get("summary", {}),
            "next_steps": next_steps,
        },
        "warnings": loaded_sources.get("warnings", []),
        "errors": [],
    }
    return briefing
