
import pytest
import pandas as pd
import numpy as np
from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec
from signal_bridge.feature_runtime import FeatureRuntime

def test_enough_lookback_produces_features():
    reg = FeatureRegistry()
    reg.register(FeatureSpec("returns", "v1", "pct_change", 5, ["close"]), lambda df: df["close"].pct_change())
    runtime = FeatureRuntime(reg, min_lookback=10)
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = runtime.compute(data, "returns_v1")
    assert result["valid"] is True
    assert "returns_v1" in result["feature_vector"]

def test_insufficient_lookback_rejects():
    reg = FeatureRegistry()
    reg.register(FeatureSpec("returns", "v1", "pct_change", 50, ["close"]), lambda df: df["close"].pct_change())
    runtime = FeatureRuntime(reg)
    data = pd.DataFrame({"close": np.arange(10, dtype=float)})
    result = runtime.compute(data, "returns_v1")
    assert result["valid"] is False
    assert any("Insufficient" in w for w in result["warnings"])

def test_missing_columns_rejects():
    reg = FeatureRegistry()
    reg.register(FeatureSpec("returns", "v1", "pct_change", 5, ["close"]), lambda df: df["close"].pct_change())
    runtime = FeatureRuntime(reg)
    data = pd.DataFrame({"open": np.arange(20, dtype=float)})
    result = runtime.compute(data, "returns_v1")
    assert result["valid"] is False

def test_feature_set_id_matches():
    reg = FeatureRegistry()
    reg.register(FeatureSpec("returns", "v1", "pct_change", 5, ["close"]), lambda df: df["close"].pct_change())
    runtime = FeatureRuntime(reg)
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = runtime.compute(data, "returns_v1")
    assert result["feature_set_id"] == "returns_v1"

def test_no_future_data_used():
    runtime = FeatureRuntime(FeatureRegistry())
    data = pd.DataFrame({"close": [1, 2, 3], "future_price": [4, 5, 6]})
    assert runtime.validate_lookahead(data) is False
