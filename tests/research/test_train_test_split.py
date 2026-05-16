
import pytest
import pandas as pd
from research_pipeline.train_test_split import TimeSeriesSplit, PurgedSplit, WalkForwardSplit

def test_time_series_split():
    df = pd.DataFrame({"a": range(100)})
    splitter = TimeSeriesSplit(n_splits=5)
    results = splitter.split(df)
    assert len(results) == 5
    for r in results:
        assert len(r.train) + len(r.test) <= 100
        assert r.method == "time_series"

def test_purged_split():
    df = pd.DataFrame({"a": range(100)})
    splitter = PurgedSplit(embargo_pct=0.02)
    result = splitter.split(df, train_pct=0.8)
    assert len(result.train) == 80
    assert len(result.purge_indices) == 2
    assert len(result.test) == 18
    assert result.method == "purged"

def test_walk_forward_split():
    df = pd.DataFrame({"a": range(100)})
    splitter = WalkForwardSplit(train_size=30, test_size=10, step_size=10)
    results = splitter.split(df)
    assert len(results) > 0
    for r in results:
        assert len(r.train) == 30
        assert len(r.test) == 10
        assert r.method == "walk_forward"

def test_no_shuffle():
    df = pd.DataFrame({"a": range(50)})
    splitter = TimeSeriesSplit(n_splits=2)
    results = splitter.split(df)
    # First test fold should be first half
    assert results[0].test_indices[0] == 0
