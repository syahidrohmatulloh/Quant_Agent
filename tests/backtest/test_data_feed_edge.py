
import pytest
from backtesting.data_feed import HistoricalDataFeed

def test_extra_field_preserved():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002, "extra": {"vol": 100}}
    ]
    feed = HistoricalDataFeed(data)
    events = list(feed)
    assert events[0].extra == {"vol": 100}

def test_datetime_object_input():
    from datetime import datetime
    data = [
        {"timestamp": datetime(2024, 1, 1, 0, 0), "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}
    ]
    feed = HistoricalDataFeed(data)
    events = list(feed)
    assert len(events) == 1
