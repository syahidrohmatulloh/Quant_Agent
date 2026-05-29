"""Cost model for simulated fills.

Conservative defaults. No claim that cost model matches real broker exactly.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CostBreakdown:
    """Structured cost breakdown for a simulated fill."""
    spread_cost: float
    slippage_cost: float
    commission: float
    total_cost: float


def compute_costs(
    quantity: float,
    fill_price: float,
    pip_size: float,
    contract_size: float,
    costs_config: Dict[str, Any],
) -> CostBreakdown:
    """Compute spread, slippage, and commission costs."""
    spread_pips = costs_config.get("spread_pips", 1.0)
    slippage_pips = costs_config.get("slippage_pips", 0.2)
    commission_per_million = costs_config.get("commission_per_million", 30.0)
    min_commission = costs_config.get("min_commission", 0.0)

    # pip_value = pip_size per unit * contract_size
    pip_value = pip_size * contract_size

    spread_cost = spread_pips * pip_value * quantity
    slippage_cost = slippage_pips * pip_value * quantity

    notional = quantity * fill_price * contract_size
    commission = commission_per_million * notional / 1_000_000.0
    commission = max(commission, min_commission)

    total = spread_cost + slippage_cost + commission

    return CostBreakdown(
        spread_cost=round(spread_cost, 4),
        slippage_cost=round(slippage_cost, 4),
        commission=round(commission, 4),
        total_cost=round(total, 4),
    )
