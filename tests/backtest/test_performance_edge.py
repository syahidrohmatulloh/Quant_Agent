
import pytest
from backtesting.performance import PerformanceAnalyzer

def test_no_trades():
    perf = PerformanceAnalyzer([], [100000], ["t1"])
    s = perf.summary()
    assert s["total_trades"] == 0
    assert s["win_rate"] == 0.0

def test_single_trade():
    perf = PerformanceAnalyzer([{"pnl": 100}], [100000, 100100], ["t1", "t2"])
    s = perf.summary()
    assert s["total_trades"] == 1
    assert s["win_rate"] == 1.0

def test_all_losses():
    perf = PerformanceAnalyzer([{"pnl": -100}, {"pnl": -50}], [100000, 99900, 99850], ["t1", "t2", "t3"])
    s = perf.summary()
    assert s["win_rate"] == 0.0
    assert s["expectancy"] == -75.0
