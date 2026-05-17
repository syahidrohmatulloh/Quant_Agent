import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test multi-factor ranking strategy.
"""
import pytest
from strategies.factors import MultiFactorRanking
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


def test_multi_factor_ranking():
    cfg = StrategyConfig(name="mf", symbols=["EURUSD", "USDJPY"], params={"lookback": 10, "top_n": 1})
    strat = MultiFactorRanking(cfg)
    data = {
        "EURUSD": _make_bars(30, "up", 1.1000),
        "USDJPY": _make_bars(30, "down", 110.0)
    }
    result = strat.generate(data)
    assert len(result.signals) == 2
    longs = [s for s in result.signals if s.signal == "long"]
    shorts = [s for s in result.signals if s.signal == "short"]
    assert len(longs) >= 1 or len(shorts) >= 1
