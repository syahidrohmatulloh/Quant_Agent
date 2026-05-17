import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test trend-following strategies with synthetic data.
"""
import pytest
from strategies.trend import TimeSeriesMomentum, MACrossover, ChannelBreakout
from strategies.base import StrategyConfig


def _make_bars(n: int, trend: str = "up") -> list:
    from datetime import datetime
    bars = []
    price = 1.1000
    for i in range(n):
        if trend == "up":
            delta = 0.001
        elif trend == "down":
            delta = -0.001
        else:
            delta = 0.0
        o = price
        c = price + delta
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        bars.append({"timestamp": datetime(2024, 1, 1 + i // 24, i % 24, 0), "open": o, "high": h, "low": l, "close": c, "volume": 1000})
        price = c
    return bars


def test_time_series_momentum_up():
    cfg = StrategyConfig(name="tsm", symbols=["EURUSD"], params={"lookback": 5, "threshold": 0.001})
    strat = TimeSeriesMomentum(cfg)
    data = {"EURUSD": _make_bars(20, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.signals[0].signal == "long"
    assert result.signals[0].weight > 0


def test_time_series_momentum_down():
    cfg = StrategyConfig(name="tsm", symbols=["EURUSD"], params={"lookback": 5, "threshold": 0.001})
    strat = TimeSeriesMomentum(cfg)
    data = {"EURUSD": _make_bars(20, "down")}
    result = strat.generate(data)
    assert result.signals[0].signal == "short"
    assert result.signals[0].weight < 0


def test_ma_crossover():
    cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 3, "slow": 10})
    strat = MACrossover(cfg)
    data = {"EURUSD": _make_bars(20, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1
    assert result.signals[0].weight >= -1.0


def test_channel_breakout():
    cfg = StrategyConfig(name="cb", symbols=["EURUSD"], params={"lookback": 5})
    strat = ChannelBreakout(cfg)
    data = {"EURUSD": _make_bars(20, "up")}
    result = strat.generate(data)
    assert len(result.signals) == 1


def test_invalid_ma_config():
    cfg = StrategyConfig(name="ma", symbols=["EURUSD"], params={"fast": 20, "slow": 5})
    strat = MACrossover(cfg)
    data = {"EURUSD": _make_bars(30, "up")}
    with pytest.raises(ValueError):
        strat.generate(data)
