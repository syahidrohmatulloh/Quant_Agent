
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.volatility_targeting import VolatilityTargeting

def test_scalar_reduces_under_high_vol():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.03, 60))  # high vol
    vt = VolatilityTargeting(target_vol=0.10, lookback=30)
    scalar = vt.compute_scalar(returns)
    assert scalar < 1.0  # should reduce

def test_scalar_allows_under_low_vol():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.005, 60))  # low vol
    vt = VolatilityTargeting(target_vol=0.10, lookback=30)
    scalar = vt.compute_scalar(returns)
    assert scalar > 1.0  # should increase up to max_leverage

def test_max_leverage_cap():
    returns = pd.Series([0.0] * 60)
    vt = VolatilityTargeting(target_vol=0.10, max_leverage=2.0)
    scalar = vt.compute_scalar(returns)
    assert scalar <= 2.0

def test_apply_weights():
    weights = pd.Series({"A": 0.5, "B": 0.5})
    returns = pd.Series(np.random.normal(0, 0.01, 60))
    vt = VolatilityTargeting(target_vol=0.10)
    scaled = vt.apply(weights, returns)
    assert abs(scaled.sum() - weights.sum() * vt.compute_scalar(returns)) < 1e-6
