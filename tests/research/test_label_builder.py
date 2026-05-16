
import pytest
import pandas as pd
import numpy as np
from research_pipeline.label_builder import LabelBuilder, LabelConfig

def test_next_return_label():
    df = pd.DataFrame({"close": [1.0, 1.1, 1.2, 1.15]})
    cfg = LabelConfig(method="next_return", horizon=1)
    builder = LabelBuilder(cfg)
    labels = builder.build(df)
    assert len(labels) == 3  # dropped last row
    assert labels.iloc[0] == pytest.approx(0.1, rel=1e-6)

def test_direction_label():
    df = pd.DataFrame({"close": [1.0, 1.1, 1.05, 1.2]})
    cfg = LabelConfig(method="direction", horizon=1)
    builder = LabelBuilder(cfg)
    labels = builder.build(df)
    assert labels.iloc[0] == 1
    assert labels.iloc[1] == -1

def test_triple_barrier_label():
    df = pd.DataFrame({"close": [1.0, 1.05, 1.02, 1.10, 0.95]})
    cfg = LabelConfig(method="triple_barrier", horizon=3, upper_barrier=0.03, lower_barrier=0.03)
    builder = LabelBuilder(cfg)
    labels = builder.build(df)
    assert len(labels) == 2  # dropped last 3 rows
    assert labels.iloc[0] == 1  # hits upper barrier

def test_metadata():
    df = pd.DataFrame({"close": [1.0, 1.1, 1.2]})
    cfg = LabelConfig(method="next_return", horizon=1)
    builder = LabelBuilder(cfg)
    builder.build(df)
    meta = builder.get_metadata()
    assert meta["method"] == "next_return"
    assert meta["horizon"] == 1
    assert meta["dropped_rows"] == 1
