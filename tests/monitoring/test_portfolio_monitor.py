
import pytest
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting
from monitoring.portfolio_monitor import PortfolioMonitor

def test_update_exposure():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = PortfolioMonitor(metrics, alert)
    monitor.update(exposure=1.5, drawdown=0.05)
    assert metrics.current_exposure == 1.5

def test_update_drawdown_alert():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = PortfolioMonitor(metrics, alert)
    monitor.update(exposure=1.5, drawdown=0.15)
    alerts = monitor.check_alerts()
    assert any(a.category == "drawdown" for a in alerts)

def test_no_alert_normal():
    metrics = LiveMetrics()
    alert = Alerting()
    monitor = PortfolioMonitor(metrics, alert)
    monitor.update(exposure=0.5, drawdown=0.02)
    alerts = monitor.check_alerts()
    assert len(alerts) == 0
