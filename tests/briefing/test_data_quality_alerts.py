"""Tests for data_quality_alerts.

Covers:
- low quality score alert
- missing dataset alert
- stale dataset alert
- import warning/error
- low row count
"""

from briefing.data_quality_alerts import detect_data_quality_alerts


def make_config():
    return {"alert_rules": {"alert_on_data_quality_warning": True}}


def test_low_quality_score():
    catalog = {"quality_score": 0.5, "datasets": []}
    alerts = detect_data_quality_alerts(catalog, None, make_config(), "UTC")
    assert any("Low Data Quality" in a["title"] for a in alerts)


def test_missing_dataset():
    catalog = {"datasets": [{"name": "fx_data", "status": "missing"}]}
    alerts = detect_data_quality_alerts(catalog, None, make_config(), "UTC")
    assert any("Missing Dataset" in a["title"] for a in alerts)
    assert all(a["severity"] == "CRITICAL" for a in alerts if "Missing" in a["title"])


def test_stale_dataset():
    catalog = {"datasets": [{"name": "fx_data", "status": "stale"}]}
    alerts = detect_data_quality_alerts(catalog, None, make_config(), "UTC")
    assert any("Stale Dataset" in a["title"] for a in alerts)


def test_import_warning():
    log = [{"status": "warning", "message": "slow import"}]
    alerts = detect_data_quality_alerts(None, log, make_config(), "UTC")
    assert any("Import Warning" in a["title"] for a in alerts)


def test_import_error():
    log = [{"status": "error", "message": "failed"}]
    alerts = detect_data_quality_alerts(None, log, make_config(), "UTC")
    assert any("Import Error" in a["title"] for a in alerts)
    assert all(a["severity"] == "CRITICAL" for a in alerts if "Error" in a["title"])


def test_low_row_count():
    log = [{"dataset": "small", "row_count": 50}]
    alerts = detect_data_quality_alerts(None, log, make_config(), "UTC")
    assert any("Low Row Count" in a["title"] for a in alerts)


def test_no_alerts_when_disabled():
    catalog = {"quality_score": 0.3}
    cfg = {"alert_rules": {"alert_on_data_quality_warning": False}}
    alerts = detect_data_quality_alerts(catalog, None, cfg, "UTC")
    assert alerts == []
