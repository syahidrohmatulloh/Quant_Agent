import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test mean reversion strategies with synthetic data.
"""
import pytest
from strategies.mean_reversion import ZScoreMeanReversion, RSImeanReversion
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


def test_zscore_mean_reversion():
    cfg = StrategyConfig(name="zscore", symbols=["EURUSD"], params={"lookback": 10, "threshold": 1.5})
    strat = ZScoreMeanReversion(cfg)
    data = {"EURUSD": _make_bars(30, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    s = result.signals[0]
    assert s.weight >= -1.0 and s.weight <= 1.0
    assert not (s.weight != s.weight)  # not NaN


def test_rsi_mean_reversion():
    cfg = StrategyConfig(name="rsi", symbols=["EURUSD"], params={"lookback": 10, "oversold": 30, "overbought": 70})
    strat = RSImeanReversion(cfg)
    data = {"EURUSD": _make_bars(30, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    s = result.signals[0]
    assert s.weight >= -1.0 and s.weight <= 1.0
