"""Convert Phase 15 paper decisions into simulated order intents.

Paper-only. No live trading. No order submission.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderIntent:
    """Represents a simulated order intent."""

    def __init__(
        self,
        intent_id: str,
        source_decision_id: str,
        generated_at: str,
        symbol: str,
        timeframe: str,
        side: str,
        target_weight: float,
        target_notional: float,
        reason: str,
        paper_only: bool = True,
        no_order_submission: bool = True,
    ):
        self.intent_id = intent_id
        self.source_decision_id = source_decision_id
        self.generated_at = generated_at
        self.symbol = symbol
        self.timeframe = timeframe
        self.side = side
        self.target_weight = target_weight
        self.target_notional = target_notional
        self.reason = reason
        self.paper_only = paper_only
        self.no_order_submission = no_order_submission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "source_decision_id": self.source_decision_id,
            "generated_at": self.generated_at,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "side": self.side,
            "target_weight": self.target_weight,
            "target_notional": self.target_notional,
            "reason": self.reason,
            "paper_only": self.paper_only,
            "no_order_submission": self.no_order_submission,
        }


def build_order_intents(
    decisions: List[Dict[str, Any]],
    risk_config: Dict[str, Any],
    initial_cash: float,
) -> List[OrderIntent]:
    """Convert paper decisions to order intents."""
    allow_short = risk_config.get("allow_short", True)
    max_notional_per_symbol = risk_config.get("max_notional_per_symbol", float("inf"))
    intents: List[OrderIntent] = []

    for decision in decisions:
        action = decision.get("action", "PAPER_HOLD")
        decision_id = decision.get("decision_id", "")
        symbol = decision.get("symbol", "UNKNOWN")
        timeframe = decision.get("timeframe", "UNKNOWN")
        target_weight = decision.get("target_weight", 0.0)

        intent_id = str(uuid.uuid4())[:12]
        generated_at = _now_iso()

        if action == "PAPER_LONG":
            side = "BUY"
            notional = min(target_weight * initial_cash, max_notional_per_symbol)
            reason = "PAPER_LONG decision converted to BUY intent."
        elif action == "PAPER_SHORT":
            if allow_short:
                side = "SELL"
                notional = min(target_weight * initial_cash, max_notional_per_symbol)
                reason = "PAPER_SHORT decision converted to SELL intent."
            else:
                side = "REJECTED"
                notional = 0.0
                reason = "PAPER_SHORT rejected because allow_short is false."
        elif action == "PAPER_NEUTRAL":
            side = "FLATTEN"
            notional = 0.0
            reason = "PAPER_NEUTRAL decision converted to FLATTEN intent."
        elif action == "PAPER_HOLD":
            side = "HOLD"
            notional = 0.0
            reason = "PAPER_HOLD decision; no trade intent."
        elif action == "PAPER_REJECTED":
            side = "REJECTED"
            notional = 0.0
            reason = "PAPER_REJECTED decision; no trade intent."
        else:
            side = "REJECTED"
            notional = 0.0
            reason = "Unrecognized action: " + str(action) + "."

        intents.append(
            OrderIntent(
                intent_id=intent_id,
                source_decision_id=decision_id,
                generated_at=generated_at,
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                target_weight=round(target_weight, 4),
                target_notional=round(notional, 2),
                reason=reason,
            )
        )

    return intents
