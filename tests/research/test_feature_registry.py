
import pytest
import pandas as pd
from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec

def test_register_and_calculate():
    reg = FeatureRegistry()
    spec = FeatureSpec("returns", "v1", "pct_change", 1, ["close"], no_lookahead=True)
    reg.register(spec, lambda df: df["close"].pct_change())
    df = pd.DataFrame({"close": [1.0, 1.1, 1.2]})
    result = reg.calculate("returns", "v1", df)
    assert len(result) == 3

def test_list_features():
    reg = FeatureRegistry()
    spec = FeatureSpec("ma", "v1", "rolling_mean", 5, ["close"])
    reg.register(spec, lambda df: df["close"].rolling(5).mean())
    assert "ma_v1" in reg.list_features()

def test_validate_no_lookahead():
    reg = FeatureRegistry()
    spec = FeatureSpec("lag1", "v1", "shift(1)", 1, ["close"], no_lookahead=True)
    reg.register(spec, lambda df: df["close"].shift(1))
    assert reg.validate_no_lookahead("lag1", "v1") is True

def test_missing_required_column():
    reg = FeatureRegistry()
    spec = FeatureSpec("returns", "v1", "pct_change", 1, ["close"])
    reg.register(spec, lambda df: df["close"].pct_change())
    df = pd.DataFrame({"open": [1.0, 1.1]})
    with pytest.raises(ValueError, match="Required column"):
        reg.calculate("returns", "v1", df)
