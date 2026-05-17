"""
Test CSV validator for all validation rules.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import csv
import tempfile
from datetime import datetime, timedelta
from market_data.csv_validator import validate_csv


def _write_csv(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_validate_valid_csv():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1005", "tick_volume": "1200"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name, symbol="EURUSD", timeframe="H1")
        assert result["valid"] is True
        assert result["row_count"] == 2
        assert result["inferred_symbol"] == "EURUSD"
        assert result["inferred_timeframe"] == "H1"
        os.unlink(f.name)


def test_validate_missing_required_columns():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "close": "1.1002"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "close"])
        result = validate_csv(f.name)
        assert result["valid"] is False
        assert any("Missing required columns" in e for e in result["errors"])
        os.unlink(f.name)


def test_validate_duplicate_timestamps():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
        {"time": "2024.01.15 10:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1005", "tick_volume": "1200"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert result["duplicate_count"] == 1
        assert any("Duplicate timestamp" in w for w in result["warnings"])
        os.unlink(f.name)


def test_validate_non_monotonic_timestamps():
    rows = [
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1005", "tick_volume": "1200"},
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert any("Non-monotonic" in w for w in result["warnings"])
        os.unlink(f.name)


def test_validate_nan_inf():
    rows = [
        {"time": "2024.01.15 10:00", "open": "nan", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "inf", "low": "1.1000", "close": "1.1005", "tick_volume": "1200"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert result["bad_price_count"] >= 2
        assert any("bad" in w.lower() for w in result["warnings"])
        os.unlink(f.name)


def test_validate_ohlc_anomalies():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.0990", "low": "1.1005", "close": "1.1002", "tick_volume": "1000"},
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1010", "tick_volume": "1200"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert result["price_anomaly_count"] >= 2
        os.unlink(f.name)


def test_validate_zero_prices():
    rows = [
        {"time": "2024.01.15 10:00", "open": "0.0", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert any("non-positive" in w.lower() for w in result["warnings"])
        os.unlink(f.name)


def test_validate_future_timestamp():
    future = (datetime.now() + timedelta(days=1)).strftime("%Y.%m.%d %H:%M")
    rows = [
        {"time": future, "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name)
        assert result["future_timestamp_count"] == 1
        os.unlink(f.name)


def test_validate_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        result = validate_csv(f.name)
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])
        os.unlink(f.name)


def test_validate_insufficient_bars():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = validate_csv(f.name, min_bars=5)
        assert result["valid"] is False
        assert any("Insufficient" in e for e in result["errors"])
        os.unlink(f.name)
