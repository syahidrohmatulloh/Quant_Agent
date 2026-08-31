import math
import uuid
from typing import Dict, Any


class RiskDecision:
    def __init__(self, allowed: bool, severity: str, reason: str, checks: Dict[str, Any]):
        self.risk_decision_id = str(uuid.uuid4())
        self.allowed = allowed
        self.severity = severity
        self.reason = reason
        self.checks = checks


class RiskManager:
    """Minimal fail-closed risk gate for paper execution."""

    ALLOWED_DIRECTIONS = {"buy", "sell", "long", "short"}

    def __init__(self, max_exposure: float = 10.0):
        if not math.isfinite(max_exposure) or max_exposure <= 0:
            raise ValueError("max_exposure must be a positive finite number")
        self.max_exposure = float(max_exposure)

    def evaluate(
        self,
        symbol: str,
        direction: str,
        volume: float,
        current_exposure: float = 0.0,
    ) -> RiskDecision:
        symbol = str(symbol or "").strip().upper()
        direction = str(direction or "").strip().lower()

        checks = {
            "symbol": symbol,
            "direction": direction,
            "volume": volume,
            "current_exposure": current_exposure,
            "max_exposure": self.max_exposure,
        }

        if not symbol:
            return RiskDecision(False, "high", "Missing symbol", checks)
        if direction not in self.ALLOWED_DIRECTIONS:
            return RiskDecision(False, "high", "Unsupported direction", checks)

        try:
            volume = float(volume)
            current_exposure = float(current_exposure)
        except (TypeError, ValueError):
            return RiskDecision(False, "high", "Invalid numeric exposure input", checks)

        if not math.isfinite(volume) or volume <= 0:
            return RiskDecision(False, "high", "Volume must be positive and finite", checks)
        if not math.isfinite(current_exposure) or current_exposure < 0:
            return RiskDecision(False, "high", "Current exposure must be non-negative and finite", checks)

        projected_exposure = current_exposure + volume
        checks["projected_exposure"] = projected_exposure

        if projected_exposure > self.max_exposure:
            return RiskDecision(False, "high", "Exceeds max exposure", checks)

        return RiskDecision(True, "low", "Risk checks passed", checks)
