import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test ensemble selector.
"""
import pytest
from strategies.ensemble import EnsembleSelector
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


def test_ensemble_vote():
    cfg = StrategyConfig(name="ens", symbols=["EURUSD"], params={
        "strategies": ["time_series_momentum", "ma_crossover"],
        "method": "vote",
        "time_series_momentum": {"lookback": 5, "threshold": 0.001},
        "ma_crossover": {"fast": 3, "slow": 10}
    })
    strat = EnsembleSelector(cfg)
    data = {"EURUSD": _make_bars(30, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.signals[0].symbol == "EURUSD"
    assert result.metrics["method"] == "vote"


def test_ensemble_average():
    cfg = StrategyConfig(name="ens", symbols=["EURUSD"], params={
        "strategies": ["time_series_momentum", "ma_crossover"],
        "method": "average",
        "time_series_momentum": {"lookback": 5, "threshold": 0.001},
        "ma_crossover": {"fast": 3, "slow": 10}
    })
    strat = EnsembleSelector(cfg)
    data = {"EURUSD": _make_bars(30, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.metrics["method"] == "average"


def test_ensemble_no_substrategies():
    cfg = StrategyConfig(name="ens", symbols=["EURUSD"], params={"strategies": []})
    strat = EnsembleSelector(cfg)
    data = {"EURUSD": _make_bars(30)}
    result = strat.generate(data)
    assert result.metrics.get("error") == "no sub-strategies"
