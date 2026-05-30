"""Tests for pnl_alerts.

Covers:
- negative simulated PnL threshold
- drawdown warning
- cost warning
"""

from briefing.pnl_alerts import detect_pnl_alerts


def make_config(threshold=-500.0, dd=-5.0):
    return {
        "alert_rules": {
            "alert_on_negative_simulated_pnl": True,
            "alert_on_large_drawdown": True,
            "simulated_pnl_warning_threshold": threshold,
            "drawdown_warning_threshold_pct": dd,
        }
    }


def test_negative_pnl_alert():
    pnl = [{"pnl": -600.0}]
    alerts = detect_pnl_alerts(pnl, None, make_config(), "UTC")
    assert any("Negative Simulated PnL" in a["title"] for a in alerts)


def test_drawdown_alert():
    state = {"total_pnl": 0.0, "drawdown_pct": -0.06}  # -6%, threshold is -5.0%
    alerts = detect_pnl_alerts(None, state, make_config(), "UTC")
    assert any("Drawdown" in a["title"] for a in alerts)
    assert all(a["severity"] == "CRITICAL" for a in alerts if "Drawdown" in a["title"])


def test_cost_warning():
    state = {"total_pnl": 100.0, "total_costs": 60.0, "drawdown_pct": 0.0}
    alerts = detect_pnl_alerts(None, state, make_config(), "UTC")
    assert any("Cost" in a["title"] for a in alerts)


def test_no_alert_when_pnl_above_threshold():
    pnl = [{"pnl": -100.0}]
    alerts = detect_pnl_alerts(pnl, None, make_config(), "UTC")
    assert not any("Negative Simulated PnL" in a["title"] for a in alerts)


def test_no_alerts_when_disabled():
    pnl = [{"pnl": -1000.0}]
    cfg = {
        "alert_rules": {
            "alert_on_negative_simulated_pnl": False,
            "alert_on_large_drawdown": False,
        }
    }
    alerts = detect_pnl_alerts(pnl, None, cfg, "UTC")
    assert alerts == []
