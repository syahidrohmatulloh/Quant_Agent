import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test cross-sectional momentum and relative strength.
"""
import pytest
from strategies.momentum import CrossSectionalMomentum, RelativeStrength
from strategies.base import StrategyConfig


def _make_bars(n: int, trend: str = "up", start: float = 1.1000) -> list:
    from datetime import datetime
    bars = []
    price = start
    for i in range(n):
        delta = 0.001 if trend == "up" else (-0.001 if trend == "down" else 0.0)
        o = price
        c = price + delta
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_cross_sectional_momentum():
    cfg = StrategyConfig(name="csm", symbols=["EURUSD", "USDJPY"], params={"lookback": 5, "top_n": 1})
    strat = CrossSectionalMomentum(cfg)
    data = {
        "EURUSD": _make_bars(20, "up", 1.1000),
        "USDJPY": _make_bars(20, "down", 110.0)
    }
    result = strat.generate(data)
    signals = {s.symbol: s for s in result.signals}
    assert signals["EURUSD"].signal == "long"
    assert signals["USDJPY"].signal == "short"


def test_relative_strength():
    cfg = StrategyConfig(name="rs", symbols=["EURUSD", "USDJPY"], params={"lookback": 5, "baseline": "EURUSD"})
    strat = RelativeStrength(cfg)
    data = {
        "EURUSD": _make_bars(20, "up", 1.1000),
        "USDJPY": _make_bars(20, "up", 110.0)
    }
    result = strat.generate(data)
    assert len(result.signals) == 2
