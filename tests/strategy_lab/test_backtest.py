import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test simple backtest engine with synthetic data.
"""
import pytest
from strategy_lab.backtest import SimpleBacktestEngine
from strategies.trend import MACrossover
from strategies.base import StrategyConfig


def _make_bars(n: int, trend: str = "up") -> list:
    from datetime import datetime
    bars = []
    price = 1.1000
    for i in range(n):
        delta = 0.001 if trend == "up" else (-0.001 if trend == "down" else 0.0)
        o = price
        c = price + delta
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_backtest_runs():
    cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 3, "slow": 10})
    strat = MACrossover(cfg)
    data = {"EURUSD": _make_bars(50, "up")}
    engine = SimpleBacktestEngine(data, strat, initial_balance=10000.0)
    result = engine.run()
    assert "total_return" in result
    assert "max_drawdown" in result
    assert "equity_curve" in result
    assert len(result["equity_curve"]) > 1


def test_backtest_empty_data():
    cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 3, "slow": 10})
    strat = MACrossover(cfg)
    engine = SimpleBacktestEngine({}, strat)
    result = engine.run()
    assert result["total_trades"] == 0
