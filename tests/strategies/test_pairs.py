import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test pairs trading signal.
"""
import pytest
from strategies.pairs import PairsTradingSignal
from strategies.base import StrategyConfig


def _make_bars(n: int, start: float = 1.1000, spread_drift: float = 0.0) -> list:
    from datetime import datetime
    bars = []
    price = start
    for i in range(n):
        o = price
        c = price + 0.001 + spread_drift
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_pairs_trading():
    cfg = StrategyConfig(name="pairs", symbols=["EURUSD", "USDJPY"], params={"pair": ["EURUSD", "USDJPY"], "lookback": 10, "threshold": 1.0})
    strat = PairsTradingSignal(cfg)
    data = {
        "EURUSD": _make_bars(30, 1.1000, 0.0),
        "USDJPY": _make_bars(30, 110.0, 0.0)
    }
    result = strat.generate(data)
    assert len(result.signals) == 2
    for s in result.signals:
        assert s.symbol in ("EURUSD", "USDJPY")


def test_pairs_missing_symbol():
    cfg = StrategyConfig(name="pairs", symbols=["EURUSD"], params={"pair": ["EURUSD", "GBPUSD"], "lookback": 10})
    strat = PairsTradingSignal(cfg)
    data = {"EURUSD": _make_bars(30)}
    result = strat.generate(data)
    assert result.metrics.get("error") == "missing pair data"
