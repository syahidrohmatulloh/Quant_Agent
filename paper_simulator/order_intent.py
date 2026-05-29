"""Convert paper decisions into local-only simulated order intents.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class OrderIntent:
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
        reason: str = "",
        paper_only: bool = True,
        no_order_submission: bool = True,
    ) -> None:
        self.intent_id = intent_id
        self.source_decision_id = source_decision_id
        self.generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        self.symbol = symbol
        self.timeframe = timeframe
        self.side = side
        self.target_weight = float(target_weight or 0.0)
        self.target_notional = float(target_notional or 0.0)
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


def _get_symbol_config(symbol_configs: Optional[Dict[str, Any]], symbol: str, timeframe: str) -> Dict[str, Any]:
    if not symbol_configs:
        return {}
    return (
        symbol_configs.get(symbol)
        or symbol_configs.get(symbol + "_" + timeframe)
        or symbol_configs.get((symbol, timeframe))
        or {}
    )


def build_order_intents(
    decisions: List[Dict[str, Any]],
    symbol_configs: Optional[Dict[str, Any]] = None,
    initial_cash: float = 100000.0,
    risk_config: Optional[Dict[str, Any]] = None,
) -> List[OrderIntent]:
    """Convert Phase 15 paper decisions into simulated order intents."""
    risk_config = risk_config or {}
    intents: List[OrderIntent] = []

    for d in decisions:
        action = str(d.get("action", "")).upper()
        symbol = str(d.get("symbol", "")).strip()
        timeframe = str(d.get("timeframe", "")).strip()

        if not symbol:
            continue

        if action == "PAPER_LONG":
            side = "BUY"
        elif action == "PAPER_SHORT":
            side = "SELL" if risk_config.get("allow_short", True) is not False else "REJECTED"
        elif action == "PAPER_NEUTRAL":
            side = "FLATTEN"
        elif action == "PAPER_HOLD":
            side = "HOLD"
        else:
            side = "REJECTED"

        if side == "REJECTED":
            continue

        target_weight = float(d.get("target_weight") or 0.0)
        if target_weight <= 0 and side in {"BUY", "SELL"}:
            target_weight = 0.10

        target_notional = float(d.get("target_notional") or 0.0)
        if target_notional <= 0 and side in {"BUY", "SELL"}:
            target_notional = float(initial_cash or 100000.0) * target_weight

        intent_id = "intent-" + str(d.get("decision_id") or len(intents) + 1)

        intents.append(
            OrderIntent(
                intent_id=intent_id,
                source_decision_id=str(d.get("decision_id", "")),
                generated_at=str(d.get("generated_at", "")),
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                target_weight=target_weight,
                target_notional=target_notional,
                reason=str(d.get("reason", "")),
                paper_only=True,
                no_order_submission=True,
            )
        )

    return intents
