import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test volatility strategies.
"""
import pytest
from strategies.volatility import ATRBreakout, VolatilityBreakout
from strategies.base import StrategyConfig


def _make_bars(n: int, vol: float = 0.001) -> list:
    from datetime import datetime
    import random
    random.seed(42)
    bars = []
    price = 1.1000
    for i in range(n):
        o = price
        c = price + random.uniform(-vol, vol)
        h = max(o, c) + random.uniform(0, vol)
        l = min(o, c) - random.uniform(0, vol)
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_atr_breakout():
    cfg = StrategyConfig(name="atr", symbols=["EURUSD"], params={"lookback": 10, "multiplier": 1.0})
    strat = ATRBreakout(cfg)
    data = {"EURUSD": _make_bars(30, 0.002)}
    result = strat.generate(data)
    assert len(result.signals) == 1
    s = result.signals[0]
    assert s.weight >= -1.0 and s.weight <= 1.0


def test_volatility_breakout():
    cfg = StrategyConfig(name="vol", symbols=["EURUSD"], params={"lookback": 10, "threshold": 0.01})
    strat = VolatilityBreakout(cfg)
    data = {"EURUSD": _make_bars(30, 0.002)}
    result = strat.generate(data)
    assert len(result.signals) == 1
