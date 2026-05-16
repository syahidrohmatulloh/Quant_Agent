
import pytest
from datetime import datetime
from backtesting.backtest_engine import BacktestEngine
from backtesting.data_feed import HistoricalDataFeed
from research.example_strategies import DummyAlwaysBuy

def test_engine_produces_result():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002},
        {"timestamp": "2024-01-01T00:01:00", "symbol": "EURUSD", "bid": 1.1001, "ask": 1.1003},
        {"timestamp": "2024-01-01T00:02:00", "symbol": "EURUSD", "bid": 1.1002, "ask": 1.1004},
    ]
    feed = HistoricalDataFeed(data)
    strategy = DummyAlwaysBuy()
    engine = BacktestEngine(feed, strategy, initial_balance=100000.0)
    result = engine.run()
    assert "summary" in result
    assert "trades" in result
    assert isinstance(result["trades"], list)
