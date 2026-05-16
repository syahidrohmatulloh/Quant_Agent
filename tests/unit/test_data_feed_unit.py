
import pytest
from backtesting.data_feed import HistoricalDataFeed

def test_from_list():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002},
    ]
    feed = HistoricalDataFeed(data)
    events = list(feed)
    assert len(events) == 1
    assert events[0].symbol == "EURUSD"
