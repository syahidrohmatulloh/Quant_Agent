
import pytest
from datetime import datetime
from research.example_strategies import DummyAlwaysBuy, MACrossStrategy, BreakoutStrategy
from backtesting.event import MarketEvent

def test_dummy_returns_buy():
    s = DummyAlwaysBuy()
    ev = MarketEvent(datetime(2024,1,1), "EURUSD", 1.1, 1.1002)
    sig = s.on_market_event(ev)
    assert sig.signal == "buy"

def test_ma_cross_no_signal_early():
    s = MACrossStrategy(fast=2, slow=5)
    ev = MarketEvent(datetime(2024,1,1), "EURUSD", 1.1, 1.1002)
    sig = s.on_market_event(ev)
    assert sig is None

def test_breakout_no_signal_early():
    s = BreakoutStrategy(lookback=10)
    for i in range(5):
        ev = MarketEvent(datetime(2024,1,1,i), "EURUSD", 1.1, 1.1002)
        sig = s.on_market_event(ev)
    assert sig is None
