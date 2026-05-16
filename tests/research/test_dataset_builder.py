
import pytest
import pandas as pd
from research_pipeline.dataset_builder import DatasetBuilder

def test_build_basic():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "open": 1.1000, "high": 1.1005, "low": 1.0995, "close": 1.1002},
        {"timestamp": "2024-01-01T00:01:00", "symbol": "EURUSD", "open": 1.1002, "high": 1.1008, "low": 1.1000, "close": 1.1005},
    ]
    builder = DatasetBuilder()
    meta = builder.build(data, source="ohlcv", symbols=["EURUSD"], timeframe="1m")
    assert "dataset_id" in meta
    assert meta["row_count"] == 2
    assert meta["source"] == "ohlcv"
    assert meta["data_hash"] is not None

def test_validate_empty():
    builder = DatasetBuilder()
    with pytest.raises(ValueError, match="empty"):
        builder.build([])

def test_validate_duplicate_timestamps():
    builder = DatasetBuilder()
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "open": 1.1, "high": 1.11, "low": 1.09, "close": 1.10},
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "open": 1.1, "high": 1.11, "low": 1.09, "close": 1.10},
    ]
    with pytest.raises(ValueError, match="Duplicate"):
        builder.build(data)

def test_validate_invalid_ohlc():
    builder = DatasetBuilder()
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "open": 1.1, "high": 1.09, "low": 1.11, "close": 1.10},
    ]
    with pytest.raises(ValueError, match="Invalid OHLC"):
        builder.build(data)

def test_get_data():
    data = [
        {"timestamp": "2024-01-01T00:00:00", "symbol": "EURUSD", "open": 1.1, "high": 1.11, "low": 1.09, "close": 1.10},
    ]
    builder = DatasetBuilder()
    meta = builder.build(data)
    df = builder.get(meta["dataset_id"])
    assert df is not None
    assert len(df) == 1
