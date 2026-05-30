"""PnL alerts.

All PnL references are explicitly labeled as simulated.
"""

from typing import Any, Dict, List, Optional
from briefing.alert_rules import create_alert


def detect_pnl_alerts(
    pnl_records: Optional[List[Dict[str, Any]]],
    simulator_state: Optional[Dict[str, Any]],
    config: Dict[str, Any],
    timezone_str: str = "UTC",
) -> List[Dict[str, Any]]:
    alerts = []
    rules = config.get("alert_rules", {})

    if not rules.get("alert_on_negative_simulated_pnl", True) and not rules.get("alert_on_large_drawdown", True):
        return alerts

    # Get latest PnL from records
    latest_pnl = None
    if pnl_records:
        latest_pnl = pnl_records[-1].get("pnl", 0.0) if pnl_records else 0.0

    # Also check simulator state
    state_pnl = simulator_state.get("total_pnl", 0.0) if simulator_state else 0.0
    total_pnl = latest_pnl if latest_pnl is not None else state_pnl

    threshold = rules.get("simulated_pnl_warning_threshold", -500.0)
    if rules.get("alert_on_negative_simulated_pnl", True) and total_pnl < threshold:
        alerts.append(create_alert(
            severity="WARNING",
            category="pnl",
            title="Negative Simulated PnL Alert",
            message=f"Simulated PnL {total_pnl:.2f} below threshold {threshold:.2f} (paper-only, not real money).",
            source="paper_simulator_pnl",
            timezone_str=timezone_str,
            extra={"simulated_pnl": total_pnl, "threshold": threshold},
        ))

    # Drawdown
    drawdown_pct = simulator_state.get("drawdown_pct", 0.0) if simulator_state else 0.0
    dd_threshold = rules.get("drawdown_warning_threshold_pct", -5.0)
    if rules.get("alert_on_large_drawdown", True) and (drawdown_pct * 100) < dd_threshold:
        alerts.append(create_alert(
            severity="CRITICAL",
            category="pnl",
            title="Large Drawdown Warning",
            message=f"Simulated drawdown {drawdown_pct:.2%} exceeds threshold {dd_threshold:.2%} (paper-only).",
            source="paper_simulator_state",
            timezone_str=timezone_str,
            extra={"drawdown_pct": drawdown_pct, "threshold": dd_threshold},
        ))

    # Cost warning
    costs = simulator_state.get("total_costs", 0.0) if simulator_state else 0.0
    if costs > abs(total_pnl) * 0.5 and total_pnl != 0:
        alerts.append(create_alert(
            severity="INFO",
            category="pnl",
            title="High Cost Ratio",
            message=f"Simulated costs {costs:.2f} are high relative to PnL {total_pnl:.2f} (paper-only).",
            source="paper_simulator_state",
            timezone_str=timezone_str,
            extra={"costs": costs, "simulated_pnl": total_pnl},
        ))

    return alerts
