import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test regime filter strategies.
"""
import pytest
from strategies.regime import VolatilityRegime, TrendRegime, RiskOnOffFilter
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


def test_volatility_regime():
    cfg = StrategyConfig(name="vr", symbols=["EURUSD"], params={"lookback": 10, "high_threshold": 0.02})
    strat = VolatilityRegime(cfg)
    data = {"EURUSD": _make_bars(30, 0.001)}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.signals[0].meta.get("regime") in ("low_vol", "normal", "high_vol")


def test_trend_regime():
    cfg = StrategyConfig(name="tr", symbols=["EURUSD"], params={"lookback": 10})
    strat = TrendRegime(cfg)
    data = {"EURUSD": _make_bars(30, 0.001)}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.signals[0].meta.get("regime") in ("uptrend", "downtrend", "ranging")


def test_risk_on_off():
    cfg = StrategyConfig(name="ro", symbols=["EURUSD", "USDJPY"], params={"safe_haven": "USDJPY", "lookback": 10})
    strat = RiskOnOffFilter(cfg)
    data = {
        "EURUSD": _make_bars(30, 0.001),
        "USDJPY": _make_bars(30, 0.001)
    }
    result = strat.generate(data)
    assert len(result.signals) == 2
