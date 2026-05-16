
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.allocation_engine import AllocationEngine
from portfolio_optimization.constraints import Constraints

def test_allocation_produces_weights():
    np.random.seed(42)
    returns = pd.DataFrame({
        "EURUSD": np.random.normal(0, 0.01, 100),
        "GBPUSD": np.random.normal(0, 0.012, 100)
    })
    signals = {"EURUSD": 1.0, "GBPUSD": -1.0}
    engine = AllocationEngine()
    result = engine.allocate(signals, returns)
    assert "target_weights" in result
    assert "EURUSD" in result["target_weights"]
    assert result["covariance_valid"] is True

def test_max_weight_constraint():
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.01, 100)
    })
    signals = {"A": 1.0, "B": 1.0}
    constraints = Constraints(max_weight=0.4)
    engine = AllocationEngine(constraints=constraints)
    result = engine.allocate(signals, returns)
    weights = pd.Series(result["target_weights"])
    assert all(weights.abs() <= 0.4 + 1e-6)

def test_order_intents_generated():
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.01, 100)
    })
    signals = {"A": 1.0, "B": -1.0}
    current = {"A": 0.0, "B": 0.2}
    engine = AllocationEngine()
    result = engine.allocate(signals, returns, current_positions=current)
    assert "order_intents" in result
    assert len(result["order_intents"]) > 0

def test_nan_covariance_rejected():
    returns = pd.DataFrame({
        "A": [np.nan] * 10,
        "B": [np.nan] * 10
    })
    engine = AllocationEngine()
    with pytest.raises(ValueError):
        engine.allocate({"A": 1.0}, returns)
