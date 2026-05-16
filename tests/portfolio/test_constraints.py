
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.constraints import Constraints

def test_weights_sum_within_gross():
    w = pd.Series({"A": 0.6, "B": 0.6})
    c = Constraints(max_gross_exposure=1.0)
    out = c.apply(w)
    assert out.abs().sum() <= 1.0 + 1e-6

def test_long_only_mode():
    w = pd.Series({"A": 0.5, "B": -0.3})
    c = Constraints(mode="long_only")
    out = c.apply(w)
    assert all(out >= 0)

def test_leverage_cap():
    w = pd.Series({"A": 1.5, "B": 1.5})
    c = Constraints(max_leverage=2.0)
    out = c.apply(w)
    assert out.abs().sum() <= 2.0 + 1e-6

def test_correlated_exposure_cap():
    w = pd.Series({"A": 0.4, "B": 0.4})
    c = Constraints(max_correlated_exposure=0.5)
    pairs = [("A", "B", 0.9)]
    out = c.apply(w, high_corr_pairs=pairs)
    assert abs(out["A"]) + abs(out["B"]) <= 0.5 + 1e-6
