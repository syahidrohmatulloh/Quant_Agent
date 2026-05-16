
import pytest
from datetime import datetime
from backtesting.event import MarketEvent, SignalEvent, OrderEvent, FillEvent, PositionClosedEvent

def test_market_event_creation():
    e = MarketEvent(datetime(2024,1,1), "EURUSD", 1.1, 1.1002)
    assert e.symbol == "EURUSD"
    assert e.bid == 1.1

def test_signal_event():
    e = SignalEvent(datetime(2024,1,1), "EURUSD", "buy")
    assert e.signal == "buy"

def test_fill_event():
    e = FillEvent(datetime(2024,1,1), "EURUSD", "buy", 1.0, 1.1002, 7.0)
    assert e.commission == 7.0

def test_position_closed_event():
    e = PositionClosedEvent(datetime(2024,1,1), "EURUSD", "buy", 1.0, 1.1, 1.11, 100, 7.0)
    assert e.pnl == 100
