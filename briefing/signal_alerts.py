"""Signal change alerts.

Detects signal changes, new consensus, conflicts.
No trade execution implied.
"""

from typing import Any, Dict, List, Optional
from briefing.alert_rules import create_alert


def detect_signal_alerts(
    experiment_summary: Optional[Dict[str, Any]],
    previous_signals: Optional[Dict[str, Any]],
    config: Dict[str, Any],
    timezone_str: str = "UTC",
) -> List[Dict[str, Any]]:
    alerts = []
    if not experiment_summary:
        return alerts

    rules = config.get("alert_rules", {})
    if not rules.get("alert_on_signal_change", True):
        return alerts

    signals = experiment_summary.get("signals", {})
    consensus = signals.get("consensus", "NEUTRAL")
    previous_consensus = previous_signals.get("consensus", "NEUTRAL") if previous_signals else None

    # Detect consensus change
    if previous_consensus and consensus != previous_consensus:
        alerts.append(create_alert(
            severity="WARNING",
            category="signal",
            title="Signal Consensus Changed",
            message=f"Consensus changed from {previous_consensus} to {consensus} (paper-only, no execution).",
            source="experiment_dashboard",
            timezone_str=timezone_str,
            extra={"previous": previous_consensus, "current": consensus},
        ))
    elif not previous_consensus and consensus:
        alerts.append(create_alert(
            severity="INFO",
            category="signal",
            title=f"New PAPER_{consensus} Consensus",
            message=f"Initial consensus detected: {consensus} (paper-only, no execution).",
            source="experiment_dashboard",
            timezone_str=timezone_str,
            extra={"current": consensus},
        ))

    # Detect strategy disagreement
    strategy_votes = signals.get("strategy_votes", {})
    if strategy_votes:
        votes = list(strategy_votes.values())
        unique_votes = set(votes)
        if len(unique_votes) > 1:
            alerts.append(create_alert(
                severity="INFO",
                category="signal",
                title="Strategy Disagreement Detected",
                message=f"Strategies disagree: {strategy_votes} (paper-only).",
                source="experiment_dashboard",
                timezone_str=timezone_str,
                extra={"votes": strategy_votes},
            ))

    # Detect conflict neutralization
    if signals.get("conflict_neutralized") is True:
        alerts.append(create_alert(
            severity="WARNING",
            category="signal",
            title="Conflict Neutralization Applied",
            message="Signal conflict was neutralized to NEUTRAL (paper-only).",
            source="experiment_dashboard",
            timezone_str=timezone_str,
        ))

    return alerts
