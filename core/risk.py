
import uuid
from typing import Dict, Any, Optional

class RiskDecision:
    def __init__(self, allowed: bool, severity: str, reason: str, checks: Dict[str, Any]):
        self.risk_decision_id = str(uuid.uuid4())
        self.allowed = allowed
        self.severity = severity
        self.reason = reason
        self.checks = checks

class RiskManager:
    def __init__(self, max_exposure: float = 10.0):
        self.max_exposure = max_exposure

    def evaluate(self, symbol: str, direction: str, volume: float,
                 current_exposure: float = 0.0) -> RiskDecision:
        if volume > self.max_exposure:
            return RiskDecision(False, "high", "Exceeds max exposure", {"exposure": current_exposure + volume})
        return RiskDecision(True, "low", "manual skeleton pass", {"skeleton": True})
