
import pytest
import pandas as pd
import numpy as np
from portfolio_optimization.correlation import CorrelationAnalyzer

def test_high_correlation_detected():
    np.random.seed(42)
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.01, 100) + np.random.normal(0, 0.001, 100)
    })
    # Make B highly correlated with A
    returns["B"] = returns["A"] * 0.95 + np.random.normal(0, 0.002, 100)
    analyzer = CorrelationAnalyzer(threshold=0.8)
    corr = analyzer.compute(returns)
    pairs = analyzer.high_correlation_pairs(corr)
    assert len(pairs) >= 1
    assert pairs[0][0] == "A"
    assert pairs[0][1] == "B"

def test_no_high_correlation():
    np.random.seed(42)
    returns = pd.DataFrame({
        "A": np.random.normal(0, 0.01, 100),
        "B": np.random.normal(0, 0.01, 100)
    })
    analyzer = CorrelationAnalyzer(threshold=0.99)
    corr = analyzer.compute(returns)
    pairs = analyzer.high_correlation_pairs(corr)
    assert len(pairs) == 0

def test_cluster_warning():
    np.random.seed(42)
    base = np.random.normal(0, 0.01, 100)
    returns = pd.DataFrame({
        "A": base,
        "B": base * 0.95 + np.random.normal(0, 0.001, 100),
        "C": base * 0.90 + np.random.normal(0, 0.002, 100)
    })
    analyzer = CorrelationAnalyzer(threshold=0.8)
    corr = analyzer.compute(returns)
    clusters = analyzer.cluster_warning(corr)
    assert len(clusters) > 0
