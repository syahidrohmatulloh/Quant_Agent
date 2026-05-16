
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.covariance import CovarianceEstimator

def test_sample_covariance():
    np.random.seed(42)
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.02, 100)
    })
    est = CovarianceEstimator(method="sample")
    cov = est.estimate(returns)
    assert cov.shape == (2, 2)
    assert est.is_valid(cov)

def test_ewm_covariance():
    np.random.seed(42)
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.02, 100)
    })
    est = CovarianceEstimator(method="ewm", halflife=30)
    cov = est.estimate(returns)
    assert cov.shape == (2, 2)

def test_empty_data_rejected():
    est = CovarianceEstimator()
    with pytest.raises(ValueError, match="empty"):
        est.estimate(pd.DataFrame())

def test_nan_data_rejected():
    est = CovarianceEstimator()
    returns = pd.DataFrame({"A": [np.nan, np.nan, np.nan]})
    with pytest.raises(ValueError, match="empty"):
        est.estimate(returns)
