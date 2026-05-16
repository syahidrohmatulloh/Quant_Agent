
import pytest
from research.example_strategies import DummyAlwaysBuy, MACrossStrategy, BreakoutStrategy
from backtesting.event import MarketEvent
from datetime import datetime

def test_dummy_always_buy():
    s = DummyAlwaysBuy()
    ev = MarketEvent(datetime(2024, 1, 1), "EURUSD", 1.1, 1.1002)
    sig = s.on_market_event(ev)
    assert sig.signal == "buy"

def test_ma_cross_buy():
    s = MACrossStrategy(fast=2, slow=3)
    for i in range(5):
        ev = MarketEvent(datetime(2024, 1, 1, i), "EURUSD", 1.0 + i*0.001, 1.0 + i*0.001 + 0.0002)
        sig = s.on_market_event(ev)
    assert sig is not None
    assert sig.signal in ("buy", "sell")

def test_breakout():
    s = BreakoutStrategy(lookback=3)
    for i in range(5):
        ev = MarketEvent(datetime(2024, 1, 1, i), "EURUSD", 1.0 + i*0.001, 1.0 + i*0.001 + 0.0002)
        sig = s.on_market_event(ev)
    assert sig is not None
