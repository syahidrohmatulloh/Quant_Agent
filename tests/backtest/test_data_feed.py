
import pytest
from backtesting.data_feed import HistoricalDataFeed
from datetime import datetime

def test_valid_data():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002},
        {"timestamp": "2024-01-01T00:01:00", "symbol": "EURUSD", "bid": 1.1001, "ask": 1.1003},
    ]
    feed = HistoricalDataFeed(data)
    events = list(feed)
    assert len(events) == 2
    assert events[0].bid == 1.1000
    assert events[0].ask >= events[0].bid

def test_invalid_ask_below_bid():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1002, "ask": 1.1000},
    ]
    with pytest.raises(AssertionError):
        HistoricalDataFeed(data)
