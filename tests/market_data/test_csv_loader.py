"""
Test CSV loader with various formats.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import csv
import tempfile
from datetime import datetime
from market_data.csv_loader import load_csv, load_csv_strategy_shape


def _write_csv(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_load_valid_csv():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1005", "tick_volume": "1200"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = load_csv(f.name, symbol="EURUSD", timeframe="H1")
        assert len(result) == 2
        assert result[0]["symbol"] == "EURUSD"
        assert result[0]["timeframe"] == "H1"
        assert result[0]["open"] == 1.1000
        assert isinstance(result[0]["timestamp"], datetime)
        os.unlink(f.name)


def test_load_csv_timestamp_alias():
    rows = [
        {"timestamp": "2024-01-15 10:00:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["timestamp", "open", "high", "low", "close", "volume"])
        result = load_csv(f.name)
        assert len(result) == 1
        assert result[0]["timestamp"].year == 2024
        os.unlink(f.name)


def test_load_csv_missing_required():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "close": "1.1002"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "close"])
        with pytest.raises(ValueError, match="Missing required columns"):
            load_csv(f.name)
        os.unlink(f.name)


def test_load_csv_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        with pytest.raises(ValueError, match="empty"):
            load_csv(f.name)
        os.unlink(f.name)


def test_load_csv_strategy_shape():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = load_csv_strategy_shape(f.name, symbol="EURUSD", timeframe="H1")
        assert "EURUSD" in result
        assert len(result["EURUSD"]) == 1
        os.unlink(f.name)
