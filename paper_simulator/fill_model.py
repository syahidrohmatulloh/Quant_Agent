"""Simulated fill model.

No real order. No broker call. Paper-only.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from paper_simulator.cost_model import compute_costs, CostBreakdown


class FillResult:
    """Result of a simulated fill."""

    def __init__(
        self,
        fill_id: str,
        intent_id: str,
        timestamp: str,
        symbol: str,
        side: str,
        quantity: float,
        fill_price: float,
        gross_notional: float,
        spread_cost: float,
        slippage_cost: float,
        commission: float,
        total_cost: float,
        simulated: bool = True,
        paper_only: bool = True,
        no_order_submission: bool = True,
    ):
        self.fill_id = fill_id
        self.intent_id = intent_id
        self.timestamp = timestamp
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.fill_price = fill_price
        self.gross_notional = gross_notional
        self.spread_cost = spread_cost
        self.slippage_cost = slippage_cost
        self.commission = commission
        self.total_cost = total_cost
        self.simulated = simulated
        self.paper_only = paper_only
        self.no_order_submission = no_order_submission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "intent_id": self.intent_id,
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "fill_price": self.fill_price,
            "gross_notional": self.gross_notional,
            "spread_cost": self.spread_cost,
            "slippage_cost": self.slippage_cost,
            "commission": self.commission,
            "total_cost": self.total_cost,
            "simulated": self.simulated,
            "paper_only": self.paper_only,
            "no_order_submission": self.no_order_submission,
        }


def simulate_fill(
    intent: "paper_simulator.order_intent.OrderIntent",
    price: Optional[float],
    costs_config: Dict[str, Any],
    symbol_config: Dict[str, Any],
    fill_price_mode: str = "next_close",
) -> Optional[FillResult]:
    """Simulate a fill for an order intent."""
    if price is None:
        return None
    if intent.side in ("HOLD", "REJECTED"):
        return None
    if price <= 0:
        return None

    quantity = intent.target_notional / price if price > 0 else 0.0
    if quantity <= 0:
        return None

    fill_id = str(uuid.uuid4())[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    pip_size = symbol_config.get("pip_size", 0.0001)
    contract_size = symbol_config.get("contract_size", 100000)

    costs = compute_costs(
        quantity=quantity,
        fill_price=price,
        pip_size=pip_size,
        contract_size=contract_size,
        costs_config=costs_config,
    )

    gross_notional = quantity * price * contract_size
    total_cost = costs.spread_cost + costs.slippage_cost + costs.commission

    return FillResult(
        fill_id=fill_id,
        intent_id=intent.intent_id,
        timestamp=timestamp,
        symbol=intent.symbol,
        side=intent.side,
        quantity=round(quantity, 6),
        fill_price=round(price, 6),
        gross_notional=round(gross_notional, 2),
        spread_cost=round(costs.spread_cost, 4),
        slippage_cost=round(costs.slippage_cost, 4),
        commission=round(costs.commission, 4),
        total_cost=round(total_cost, 4),
    )
