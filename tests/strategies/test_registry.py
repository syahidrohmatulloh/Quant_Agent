import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test strategy registry loading and validation.
"""
import pytest
from strategies.registry import StrategyRegistry
from strategies.base import StrategyConfig


def test_registry_lists_strategies():
    names = StrategyRegistry.list_strategies()
    assert isinstance(names, list)
    assert len(names) >= 10


def test_registry_get_existing():
    cls = StrategyRegistry.get("time_series_momentum")
    assert cls is not None


def test_registry_get_missing_raises():
    with pytest.raises(KeyError):
        StrategyRegistry.get("nonexistent_strategy")


def test_registry_validate_all():
    result = StrategyRegistry.validate_all()
    assert isinstance(result, dict)
    for name, info in result.items():
        assert info["status"] == "ok", f"{name} failed: {info}"


def test_registry_is_registered():
    assert StrategyRegistry.is_registered("ma_crossover")
    assert not StrategyRegistry.is_registered("fake")
