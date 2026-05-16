
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.risk_parity import RiskParityAllocator

def test_weights_sum_to_one():
    cov = pd.DataFrame({
        "A": [0.01, 0.005],
        "B": [0.005, 0.02]
    }, index=["A", "B"])
    allocator = RiskParityAllocator()
    w = allocator.allocate(cov)
    assert abs(w.sum() - 1.0) < 1e-6
    assert all(w >= 0)

def test_equal_risk_contribution_weights():
    cov = pd.DataFrame({
        "A": [0.01, 0.005],
        "B": [0.005, 0.02]
    }, index=["A", "B"])
    allocator = RiskParityAllocator()
    w = allocator.equal_risk_contribution(cov)
    assert abs(w.sum() - 1.0) < 1e-6
    assert all(w >= 0)

def test_more_assets():
    n = 5
    cov = pd.DataFrame(np.eye(n) * 0.01 + np.random.rand(n, n) * 0.001)
    cov = cov @ cov.T  # make PSD
    cov.index = [f"S{i}" for i in range(n)]
    cov.columns = cov.index
    allocator = RiskParityAllocator()
    w = allocator.allocate(cov)
    assert abs(w.sum() - 1.0) < 1e-6
