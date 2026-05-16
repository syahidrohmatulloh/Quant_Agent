
from abc import ABC, abstractmethod
from backtesting.event import MarketEvent, FillEvent, PositionClosedEvent, SignalEvent

class StrategyBase(ABC):
    @abstractmethod
    def on_market_event(self, event: MarketEvent) -> SignalEvent:
        pass

    def on_fill_event(self, fill: FillEvent):
        pass

    def on_position_closed(self, event: PositionClosedEvent):
        pass
