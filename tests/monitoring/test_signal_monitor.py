
import pytest
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting
from monitoring.signal_monitor import SignalMonitor

def test_on_signal_generated():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = SignalMonitor(metrics, alert)
    monitor.on_signal({"generated": True, "confidence": 0.7})
    assert metrics.signals_generated == 1

def test_on_signal_rejected():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = SignalMonitor(metrics, alert)
    monitor.on_signal({"generated": False, "reason": "risk"})
    assert metrics.signals_rejected == 1

def test_check_alerts():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = SignalMonitor(metrics, alert)
    for _ in range(5):
        monitor.on_signal({"generated": False, "reason": "risk"})
    monitor.on_signal({"generated": True, "confidence": 0.7})
    alerts = monitor.check_alerts()
    assert len(alerts) >= 1
