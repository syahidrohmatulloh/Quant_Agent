
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.audit import AuditLogger

class PaperSignalExecutor:
    def __init__(self,
                 broker: PaperBroker,
                 risk_manager: RiskManager,
                 audit: AuditLogger,
                 max_signals_per_minute: int = 10,
                 circuit_breaker: bool = False):
        self.broker = broker
        self.risk_manager = risk_manager
        self.audit = audit
        self.max_signals_per_minute = max_signals_per_minute
        self.circuit_breaker = circuit_breaker
        self._signal_count = 0
        self._last_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    def execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        # Audit: signal generated
        self.audit.log("signal_generated", request_id, "system", "system", signal)

        # Circuit breaker
        if self.circuit_breaker:
            self.audit.log("signal_rejected", request_id, "system", "system", {"reason": "circuit_breaker_open"})
            return {"executed": False, "reason": "Circuit breaker open", "request_id": request_id}

        # Rate limit
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if now != self._last_minute:
            self._signal_count = 0
            self._last_minute = now
        self._signal_count += 1
        if self._signal_count > self.max_signals_per_minute:
            self.audit.log("signal_rejected", request_id, "system", "system", {"reason": "rate_limit"})
            return {"executed": False, "reason": "Rate limit exceeded", "request_id": request_id}

        # Check signal was routed to paper
        if signal.get("destination") != "paper":
            self.audit.log("signal_rejected", request_id, "system", "system", {"reason": "not_routed_to_paper"})
            return {"executed": False, "reason": "Signal not routed to paper", "request_id": request_id}

        # Risk check
        symbol = signal.get("signal", {}).get("symbol", "UNKNOWN")
        direction = signal.get("signal", {}).get("signal", "hold")
        volume = 1.0
        risk = self.risk_manager.evaluate(symbol, direction, volume)
        if not risk.allowed:
            self.audit.log("signal_rejected", request_id, "system", "system", {"reason": "risk_rejected", "risk_decision_id": risk.risk_decision_id})
            return {"executed": False, "reason": "Risk check failed", "request_id": request_id}

        # Execute on paper broker
        price = 1.1000  # placeholder
        oid, pid = self.broker.open_position(symbol, direction, volume, price)
        self.audit.log("paper_order_created", request_id, "system", "system", {
            "order_id": oid,
            "position_id": pid,
            "symbol": symbol,
            "direction": direction,
            "volume": volume,
            "price": price
        })
        return {
            "executed": True,
            "destination": "paper",
            "broker_order_id": oid,
            "broker_position_id": pid,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def set_circuit_breaker(self, open: bool):
        self.circuit_breaker = open
