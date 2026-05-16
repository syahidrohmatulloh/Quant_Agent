
import pytest
from backtesting.performance import PerformanceAnalyzer

def test_mixed_trades():
    trades = [
        {"pnl": 100}, {"pnl": -50}, {"pnl": 200}, {"pnl": -30}
    ]
    equity = [100000, 100100, 100050, 100250, 100220]
    timestamps = ["t1", "t2", "t3", "t4", "t5"]
    perf = PerformanceAnalyzer(trades, equity, timestamps)
    summary = perf.summary()
    assert summary["total_trades"] == 4
    assert summary["win_rate"] == 0.5
    assert summary["expectancy"] == 55.0
    assert summary["max_drawdown"] >= 0.0
