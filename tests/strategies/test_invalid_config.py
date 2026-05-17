import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test invalid configs fail safely.
"""
import pytest
from strategies.base import StrategyConfig
from strategies.trend import MACrossover


def test_invalid_timeframe():
    cfg = StrategyConfig(name="ma", symbols=["EURUSD"], timeframe="INVALID")
    with pytest.raises(ValueError):
        cfg.validate()


def test_empty_symbols():
    cfg = StrategyConfig(name="ma", symbols=[])
    with pytest.raises(ValueError):
        cfg.validate()
