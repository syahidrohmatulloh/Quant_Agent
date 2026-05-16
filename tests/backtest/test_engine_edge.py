
import pytest
from backtesting.backtest_engine import BacktestEngine
from backtesting.data_feed import HistoricalDataFeed
from research.example_strategies import DummyAlwaysBuy

def test_empty_data():
    feed = HistoricalDataFeed([])
    engine = BacktestEngine(feed, DummyAlwaysBuy())
    result = engine.run()
    assert result["summary"]["total_trades"] == 0

def test_single_bar():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}
    ]
    feed = HistoricalDataFeed(data)
    engine = BacktestEngine(feed, DummyAlwaysBuy())
    result = engine.run()
    assert result["summary"]["total_trades"] >= 0
