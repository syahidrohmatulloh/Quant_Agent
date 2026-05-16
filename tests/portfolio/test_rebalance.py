
import pytest
from portfolio_optimization.rebalance import RebalanceEngine

def test_rebalance_needed_when_drift_high():
    engine = RebalanceEngine(threshold=0.02)
    current = {"A": 0.3, "B": 0.7}
    target = {"A": 0.5, "B": 0.5}
    assert engine.should_rebalance(current, target) is True

def test_no_rebalance_when_within_tolerance():
    engine = RebalanceEngine(threshold=0.05)
    current = {"A": 0.31, "B": 0.69}
    target = {"A": 0.30, "B": 0.70}
    assert engine.should_rebalance(current, target) is False

def test_min_trade_threshold():
    engine = RebalanceEngine(threshold=0.01, min_trade=0.05)
    current = {"A": 0.50, "B": 0.50}
    target = {"A": 0.52, "B": 0.48}
    result = engine.generate_orders(current, target)
    assert result["rebalance_needed"] is False  # delta 0.02 < min_trade 0.05

def test_orders_generated():
    engine = RebalanceEngine(threshold=0.01, min_trade=0.001)
    current = {"A": 0.0, "B": 1.0}
    target = {"A": 0.5, "B": 0.5}
    result = engine.generate_orders(current, target)
    assert result["rebalance_needed"] is True
    assert "A" in result["orders"]
    assert result["orders"]["A"] == pytest.approx(0.5, abs=1e-6)
