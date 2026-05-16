
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class Alert:
    level: str  # info, warning, critical
    category: str
    message: str
    timestamp: str
    value: float = 0.0

class Alerting:
    def __init__(self):
        self.alerts: List[Alert] = []
        self.thresholds = {
            "rejection_rate": 0.3,
            "drawdown": 0.1,
            "drift": 3.0,
            "model_unavailable": 1,
            "feature_missing": 5,
            "circuit_breaker": 1,
            "high_correlation_exposure": 0.5
        }

    def check_rejection_rate(self, metrics: Dict[str, Any]) -> List[Alert]:
        total = metrics.get("signals_generated", 0) + metrics.get("signals_rejected", 0)
        if total > 0:
            rate = metrics.get("signals_rejected", 0) / total
            if rate > self.thresholds["rejection_rate"]:
                return [Alert("warning", "rejection_rate", f"High rejection rate: {rate:.2%}", "", rate)]
        return []

    def check_drawdown(self, drawdown: float) -> List[Alert]:
        if drawdown > self.thresholds["drawdown"]:
            return [Alert("critical", "drawdown", f"Drawdown exceeded: {drawdown:.2%}", "", drawdown)]
        return []

    def check_model_unavailable(self, count: int) -> List[Alert]:
        if count >= self.thresholds["model_unavailable"]:
            return [Alert("critical", "model_unavailable", "Model unavailable detected", "", float(count))]
        return []

    def check_circuit_breaker(self, is_open: bool) -> List[Alert]:
        if is_open:
            return [Alert("critical", "circuit_breaker", "Circuit breaker is OPEN", "", 1.0)]
        return []

    def check_feature_missing(self, count: int) -> List[Alert]:
        if count >= self.thresholds["feature_missing"]:
            return [Alert("warning", "feature_missing", f"Features missing: {count}", "", float(count))]
        return []

    def check_drift(self, drift_score: float) -> List[Alert]:
        if drift_score > self.thresholds["drift"]:
            return [Alert("warning", "drift", f"Drift detected: {drift_score:.2f}", "", drift_score)]
        return []

    def check_high_correlation_exposure(self, exposure: float) -> List[Alert]:
        if exposure > self.thresholds["high_correlation_exposure"]:
            return [Alert("warning", "correlation", f"High correlated exposure: {exposure:.2f}", "", exposure)]
        return []

    def evaluate(self, metrics: Dict[str, Any]) -> List[Alert]:
        alerts = []
        alerts.extend(self.check_rejection_rate(metrics))
        alerts.extend(self.check_drawdown(metrics.get("current_drawdown", 0)))
        alerts.extend(self.check_model_unavailable(metrics.get("model_unavailable_count", 0)))
        alerts.extend(self.check_circuit_breaker(metrics.get("circuit_breaker_open", False)))
        alerts.extend(self.check_feature_missing(metrics.get("feature_missing_count", 0)))
        alerts.extend(self.check_drift(metrics.get("drift_score", 0)))
        alerts.extend(self.check_high_correlation_exposure(metrics.get("correlated_exposure", 0)))
        self.alerts.extend(alerts)
        return alerts
