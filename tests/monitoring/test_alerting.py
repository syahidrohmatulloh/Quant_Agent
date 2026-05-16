
import pytest
from monitoring.alerting import Alerting

def test_alert_on_high_rejection_rate():
    a = Alerting()
    metrics = {"signals_generated": 10, "signals_rejected": 5}
    alerts = a.check_rejection_rate(metrics)
    assert len(alerts) == 1
    assert alerts[0].category == "rejection_rate"

def test_no_alert_normal_rejection():
    a = Alerting()
    metrics = {"signals_generated": 100, "signals_rejected": 5}
    alerts = a.check_rejection_rate(metrics)
    assert len(alerts) == 0

def test_alert_on_drawdown():
    a = Alerting()
    alerts = a.check_drawdown(0.15)
    assert len(alerts) == 1
    assert alerts[0].level == "critical"

def test_no_alert_normal_drawdown():
    a = Alerting()
    alerts = a.check_drawdown(0.05)
    assert len(alerts) == 0

def test_alert_circuit_breaker():
    a = Alerting()
    alerts = a.check_circuit_breaker(True)
    assert len(alerts) == 1
    assert alerts[0].category == "circuit_breaker"

def test_alert_model_unavailable():
    a = Alerting()
    alerts = a.check_model_unavailable(2)
    assert len(alerts) == 1

def test_alert_feature_missing():
    a = Alerting()
    alerts = a.check_feature_missing(10)
    assert len(alerts) == 1

def test_evaluate_comprehensive():
    a = Alerting()
    metrics = {
        "signals_generated": 10,
        "signals_rejected": 5,
        "current_drawdown": 0.15,
        "circuit_breaker_open": True,
        "model_unavailable_count": 2,
        "feature_missing_count": 10,
        "drift_score": 4.0,
        "correlated_exposure": 0.6
    }
    alerts = a.evaluate(metrics)
    assert len(alerts) >= 5
