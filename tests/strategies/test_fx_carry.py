import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test FX carry signal with synthetic rates.
"""
import pytest
from strategies.fx_carry import FXCarrySignal
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


def test_fx_carry_with_rates():
    cfg = StrategyConfig(name="carry", symbols=["EURUSD", "USDJPY"], params={"rates": {"EURUSD": 0.02, "USDJPY": -0.01}})
    strat = FXCarrySignal(cfg)
    data = {"EURUSD": _make_bars(20), "USDJPY": _make_bars(20)}
    result = strat.generate(data)
    assert len(result.signals) == 2
    longs = [s for s in result.signals if s.signal == "long"]
    assert any(s.symbol == "EURUSD" for s in longs)


def test_fx_carry_fallback():
    cfg = StrategyConfig(name="carry", symbols=["EURUSD", "USDJPY"], params={})
    strat = FXCarrySignal(cfg)
    data = {"EURUSD": _make_bars(20), "USDJPY": _make_bars(20)}
    result = strat.generate(data)
    assert result.metrics.get("synthetic") is True
