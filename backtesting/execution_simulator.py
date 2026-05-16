
from typing import Optional
from backtesting.event import MarketEvent, OrderEvent, FillEvent

class ExecutionSimulator:
    def __init__(self, commission_per_lot: float = 7.0, slippage_pips: float = 0.5, pip_value: float = 0.0001):
        self.commission_per_lot = commission_per_lot
        self.slippage_pips = slippage_pips
        self.pip_value = pip_value

    def simulate_fill(self, order: OrderEvent, market: MarketEvent) -> FillEvent:
        if order.direction == "buy":
            base_price = market.ask
            slip = self.slippage_pips * self.pip_value
            fill_price = base_price + slip
        else:
            base_price = market.bid
            slip = self.slippage_pips * self.pip_value
            fill_price = base_price - slip
        commission = self.commission_per_lot * order.volume
        return FillEvent(
            timestamp=market.timestamp,
            symbol=order.symbol,
            direction=order.direction,
            volume=order.volume,
            fill_price=round(fill_price, 5),
            commission=commission,
            order_id=""
        )
