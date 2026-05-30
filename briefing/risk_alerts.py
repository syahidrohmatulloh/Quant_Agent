"""Risk and exposure alerts.

Generates alerts from paper simulator exposure data.
No actual broker risk claim.
"""

from typing import Any, Dict, List, Optional
from briefing.alert_rules import create_alert


def detect_risk_alerts(
    simulator_state: Optional[Dict[str, Any]],
    orchestration_summary: Optional[Dict[str, Any]],
    config: Dict[str, Any],
    timezone_str: str = "UTC",
) -> List[Dict[str, Any]]:
    alerts = []
    rules = config.get("alert_rules", {})

    # Exposure warnings from simulator state
    if simulator_state:
        exposure = simulator_state.get("exposure", {})
        gross_exposure = exposure.get("gross_exposure", 0.0)
        short_exposure = exposure.get("short_exposure", 0.0)
        symbol_concentration = exposure.get("symbol_concentration", {})

        if rules.get("alert_on_exposure_warning", True):
            if gross_exposure > 1.0:
                alerts.append(create_alert(
                    severity="WARNING",
                    category="risk",
                    title="Gross Exposure Warning",
                    message=f"Gross exposure {gross_exposure:.2%} exceeds 100% (simulated/paper-only).",
                    source="paper_simulator_state",
                    timezone_str=timezone_str,
                    extra={"gross_exposure": gross_exposure},
                ))

            if short_exposure > 0.5:
                alerts.append(create_alert(
                    severity="WARNING",
                    category="risk",
                    title="Short Exposure Warning",
                    message=f"Short exposure {short_exposure:.2%} is elevated (simulated/paper-only).",
                    source="paper_simulator_state",
                    timezone_str=timezone_str,
                    extra={"short_exposure": short_exposure},
                ))

            # Symbol concentration
            for sym, pct in (symbol_concentration or {}).items():
                if pct > 0.5:
                    alerts.append(create_alert(
                        severity="WARNING",
                        category="risk",
                        title=f"Symbol Concentration Warning: {sym}",
                        message=f"{sym} concentration {pct:.2%} exceeds 50% (simulated/paper-only).",
                        source="paper_simulator_state",
                        timezone_str=timezone_str,
                        extra={"symbol": sym, "concentration": pct},
                    ))

    # Max decision warning from orchestration
    if orchestration_summary:
        max_decisions = orchestration_summary.get("max_decisions_reached", False)
        if rules.get("alert_on_exposure_warning", True) and max_decisions:
            alerts.append(create_alert(
                severity="WARNING",
                category="risk",
                title="Max Decision Count Reached",
                message="Paper orchestration reached max decision limit (no live orders).",
                source="paper_orchestration_dashboard",
                timezone_str=timezone_str,
            ))

    return alerts
