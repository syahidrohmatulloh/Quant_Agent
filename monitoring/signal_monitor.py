
from typing import Dict, Any, List
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting

class SignalMonitor:
    def __init__(self, metrics: LiveMetrics, alerting: Alerting):
        self.metrics = metrics
        self.alerting = alerting

    def on_signal(self, signal_result: Dict[str, Any]):
        generated = signal_result.get("generated", False)
        reason = signal_result.get("reason", "")
        self.metrics.record_signal(generated, reason)
        if generated:
            self.metrics.record_prediction(signal_result.get("confidence", 0.0))

    def on_order(self, order_result: Dict[str, Any]):
        if order_result.get("executed"):
            self.metrics.record_order()

    def check_alerts(self) -> List[Any]:
        return self.alerting.evaluate(self.metrics.summary())
