
from research.strategy_base import StrategyBase
from backtesting.event import MarketEvent, SignalEvent

class DummyAlwaysBuy(StrategyBase):
    def on_market_event(self, event: MarketEvent) -> SignalEvent:
        return SignalEvent(timestamp=event.timestamp, symbol=event.symbol, signal="buy")

class MACrossStrategy(StrategyBase):
    def __init__(self, fast: int = 5, slow: int = 10):
        self.fast = fast
        self.slow = slow
        self.prices = []

    def on_market_event(self, event: MarketEvent) -> SignalEvent:
        mid = (event.bid + event.ask) / 2
        self.prices.append(mid)
        if len(self.prices) < self.slow:
            return None
        fast_ma = sum(self.prices[-self.fast:]) / self.fast
        slow_ma = sum(self.prices[-self.slow:]) / self.slow
        if fast_ma > slow_ma:
            return SignalEvent(timestamp=event.timestamp, symbol=event.symbol, signal="buy")
        elif fast_ma < slow_ma:
            return SignalEvent(timestamp=event.timestamp, symbol=event.symbol, signal="sell")
        return None

class BreakoutStrategy(StrategyBase):
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.prices = []

    def on_market_event(self, event: MarketEvent) -> SignalEvent:
        mid = (event.bid + event.ask) / 2
        self.prices.append(mid)
        if len(self.prices) < self.lookback:
            return None
        high = max(self.prices[-self.lookback:])
        low = min(self.prices[-self.lookback:])
        if mid >= high:
            return SignalEvent(timestamp=event.timestamp, symbol=event.symbol, signal="buy")
        if mid <= low:
            return SignalEvent(timestamp=event.timestamp, symbol=event.symbol, signal="sell")
        return None
