
import pytest
from datetime import datetime
from backtesting.data_feed import HistoricalDataFeed
from backtesting.backtest_engine import BacktestEngine
from research.example_strategies import MACrossStrategy

def test_full_backtest_flow():
    data = [
        {"timestamp": f"2024-01-01T{i:02d}:00:00", "symbol": "EURUSD", "bid": 1.1000 + i*0.0001, "ask": 1.1002 + i*0.0001}
        for i in range(24)
    ]
    feed = HistoricalDataFeed(data)
    strategy = MACrossStrategy(fast=3, slow=5)
    engine = BacktestEngine(feed, strategy, initial_balance=100000.0)
    result = engine.run()
    assert "summary" in result
    assert result["summary"]["total_trades"] >= 0
