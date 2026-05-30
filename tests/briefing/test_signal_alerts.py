"""Tests for signal_alerts.

Covers:
- signal alert detects PAPER_LONG / PAPER_SHORT / PAPER_NEUTRAL
- signal conflict neutralization alert
- strategy disagreement
"""

from briefing.signal_alerts import detect_signal_alerts


def make_config():
    return {"alert_rules": {"alert_on_signal_change": True}}


def test_detects_new_consensus():
    exp = {"signals": {"consensus": "LONG", "strategy_votes": {"s1": "LONG"}}}
    alerts = detect_signal_alerts(exp, None, make_config(), "UTC")
    assert any(a["title"] == "New PAPER_LONG Consensus" for a in alerts)


def test_detects_consensus_change():
    exp = {"signals": {"consensus": "SHORT", "strategy_votes": {"s1": "SHORT"}}}
    prev = {"consensus": "LONG"}
    alerts = detect_signal_alerts(exp, prev, make_config(), "UTC")
    assert any("Changed" in a["title"] for a in alerts)


def test_detects_strategy_disagreement():
    exp = {"signals": {"consensus": "NEUTRAL", "strategy_votes": {"s1": "LONG", "s2": "SHORT"}}}
    alerts = detect_signal_alerts(exp, None, make_config(), "UTC")
    assert any("Disagreement" in a["title"] for a in alerts)


def test_detects_conflict_neutralization():
    exp = {"signals": {"consensus": "NEUTRAL", "conflict_neutralized": True}}
    alerts = detect_signal_alerts(exp, None, make_config(), "UTC")
    assert any("Conflict Neutralization" in a["title"] for a in alerts)


def test_no_alerts_when_disabled():
    exp = {"signals": {"consensus": "LONG"}}
    cfg = {"alert_rules": {"alert_on_signal_change": False}}
    alerts = detect_signal_alerts(exp, None, cfg, "UTC")
    assert alerts == []
