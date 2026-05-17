import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test validation helpers.
"""
import pytest
from strategy_lab.validation import validate_registry, validate_config, validate_signal_shape, validate_no_nan_inf
from strategies.base import StrategyConfig, StrategyResult, StrategySignal
from datetime import datetime


def test_validate_registry():
    result = validate_registry()
    assert isinstance(result, dict)
    for name, info in result.items():
        assert info["status"] == "ok"


def test_validate_config_ok():
    cfg = StrategyConfig(name="test", symbols=["EURUSD"])
    assert validate_config(cfg) == []


def test_validate_config_bad_timeframe():
    cfg = StrategyConfig(name="test", symbols=["EURUSD"], timeframe="INVALID")
    errs = validate_config(cfg)
    assert any("timeframe" in e for e in errs)


def test_validate_signal_shape():
    sig = StrategySignal(timestamp=datetime.now(), symbol="EURUSD", signal="long", weight=0.5)
    result = StrategyResult(signals=[sig])
    assert validate_signal_shape(result, ["EURUSD"]) == []


def test_validate_signal_shape_missing_symbol():
    sig = StrategySignal(timestamp=datetime.now(), symbol="EURUSD", signal="long", weight=0.5)
    result = StrategyResult(signals=[sig])
    errs = validate_signal_shape(result, ["EURUSD", "USDJPY"])
    assert any("Missing" in e for e in errs)


def test_validate_no_nan_inf():
    sig = StrategySignal(timestamp=datetime.now(), symbol="EURUSD", signal="long", weight=0.5)
    result = StrategyResult(signals=[sig])
    assert validate_no_nan_inf(result) == []
