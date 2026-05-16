
from typing import Dict, Any, List
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting

class PortfolioMonitor:
    def __init__(self, metrics: LiveMetrics, alerting: Alerting):
        self.metrics = metrics
        self.alerting = alerting

    def update(self, exposure: float, drawdown: float, pnl: float = 0.0):
        self.metrics.update_exposure(exposure)
        self.metrics.update_drawdown(drawdown)
        if pnl != 0:
            self.metrics.record_pnl(pnl)

    def check_alerts(self) -> List[Any]:
        return self.alerting.evaluate(self.metrics.summary())
