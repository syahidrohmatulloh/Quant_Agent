"""Tests for risk_alerts.

Covers:
- exposure warning alert
- symbol concentration warning
- max decision warning
"""

from briefing.risk_alerts import detect_risk_alerts


def make_config():
    return {"alert_rules": {"alert_on_exposure_warning": True}}


def test_gross_exposure_warning():
    state = {"exposure": {"gross_exposure": 1.5, "short_exposure": 0.1, "symbol_concentration": {}}}
    alerts = detect_risk_alerts(state, None, make_config(), "UTC")
    assert any("Gross Exposure" in a["title"] for a in alerts)


def test_short_exposure_warning():
    state = {"exposure": {"gross_exposure": 0.5, "short_exposure": 0.6, "symbol_concentration": {}}}
    alerts = detect_risk_alerts(state, None, make_config(), "UTC")
    assert any("Short Exposure" in a["title"] for a in alerts)


def test_symbol_concentration_warning():
    state = {"exposure": {"gross_exposure": 0.5, "short_exposure": 0.1, "symbol_concentration": {"EURUSD": 0.6}}}
    alerts = detect_risk_alerts(state, None, make_config(), "UTC")
    assert any("EURUSD" in a["title"] for a in alerts)


def test_max_decision_warning():
    orch = {"max_decisions_reached": True}
    alerts = detect_risk_alerts(None, orch, make_config(), "UTC")
    assert any("Max Decision" in a["title"] for a in alerts)


def test_no_alerts_when_disabled():
    state = {"exposure": {"gross_exposure": 2.0}}
    cfg = {"alert_rules": {"alert_on_exposure_warning": False}}
    alerts = detect_risk_alerts(state, None, cfg, "UTC")
    assert alerts == []
