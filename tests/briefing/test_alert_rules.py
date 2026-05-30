"""Tests for alert_rules.

Covers:
- alert creation shape
- filter alerts by severity
"""

from briefing.alert_rules import create_alert, filter_alerts


def test_create_alert_shape():
    alert = create_alert(
        severity="WARNING",
        category="risk",
        title="Test",
        message="Msg",
        source="test",
        timezone_str="Asia/Jakarta",
    )
    assert alert["severity"] == "WARNING"
    assert alert["category"] == "risk"
    assert alert["title"] == "Test"
    assert alert["paper_only"] is True
    assert alert["data_only"] is True
    assert alert["no_order_submission"] is True
    assert "generated_at" in alert


def test_filter_alerts_limits_count():
    alerts = [
        create_alert("INFO", "system", f"A{i}", "msg", "src") for i in range(25)
    ]
    filtered = filter_alerts(alerts, max_alerts=20)
    assert len(filtered) == 20


def test_filter_alerts_sorts_severity():
    alerts = [
        create_alert("INFO", "system", "Info", "msg", "src"),
        create_alert("CRITICAL", "system", "Crit", "msg", "src"),
        create_alert("WARNING", "system", "Warn", "msg", "src"),
    ]
    filtered = filter_alerts(alerts, max_alerts=2)
    assert filtered[0]["severity"] == "CRITICAL"
    assert filtered[1]["severity"] == "WARNING"
