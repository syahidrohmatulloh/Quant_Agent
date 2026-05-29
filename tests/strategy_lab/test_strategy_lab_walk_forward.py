import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test walk-forward validation.
"""
import pytest
from strategy_lab.walk_forward import WalkForwardValidation
from strategies.trend import MACrossover
from strategies.base import StrategyConfig


def _make_bars(n: int) -> list:
    from datetime import datetime
    bars = []
    price = 1.1000
    for i in range(n):
        o = price
        c = price + 0.001
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_walk_forward_runs():
    def factory():
        cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 3, "slow": 10})
        return MACrossover(cfg)
    data = {"EURUSD": _make_bars(200)}
    wf = WalkForwardValidation(data, factory, n_folds=3)
    results = wf.run()
    assert len(results) > 0
    for r in results:
        assert "fold" in r
        assert "train_size" in r
        assert "test_size" in r


def test_walk_forward_insufficient_data():
    def factory():
        cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 3, "slow": 10})
        return MACrossover(cfg)
    data = {"EURUSD": _make_bars(5)}
    wf = WalkForwardValidation(data, factory, n_folds=3)
    results = wf.run()
    assert results == []
