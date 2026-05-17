import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import pytest
import csv
import tempfile
from datetime import datetime
from broker_integration.mt5.mt5_csv_loader import load_mt5_csv, load_mt5_csv_multi, load_mt5_csvl


def _write_csv(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_load_mt5_csv_basic():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000", "spread": "2", "real_volume": "5000"},
        {"time": "2024.01.15 11:00", "open": "1.1002", "high": "1.1008", "low": "1.1000", "close": "1.1005", "tick_volume": "1200", "spread": "2", "real_volume": "6000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"])
        result = load_mt5_csv(f.name, symbol="EURUSD", timeframe="H1")
        assert len(result) == 2
        assert result[0]["symbol"] == "EURUSD"
        assert result[0]["timeframe"] == "H1"
        assert result[0]["source"] == "mt5_csv"
        assert result[0]["open"] == 1.1000
        assert result[0]["tick_volume"] == 1000
        assert result[0]["spread"] == 2
        assert result[0]["real_volume"] == 5000
        assert isinstance(result[0]["timestamp"], datetime)
        os.unlink(f.name)


def test_load_mt5_csv_timestamp_alias():
    rows = [
        {"timestamp": "2024-01-15 10:00:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["timestamp", "open", "high", "low", "close", "volume"])
        result = load_mt5_csv(f.name)
        assert len(result) == 1
        assert result[0]["timestamp"].year == 2024
        os.unlink(f.name)


def test_load_mt5_csv_missing_required():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "close": "1.1002"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "close"])
        with pytest.raises(ValueError, match="Missing required columns"):
            load_mt5_csv(f.name)
        os.unlink(f.name)


def test_load_mt5_csv_missing_timestamp():
    rows = [
        {"open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["open", "high", "low", "close"])
        with pytest.raises(ValueError, match="Missing timestamp column"):
            load_mt5_csv(f.name)
        os.unlink(f.name)


def test_load_mt5_csv_multi():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "low": "1.0995", "close": "1.1002", "tick_volume": "1000"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = load_mt5_csv_multi(f.name, symbol="EURUSD", timeframe="H1")
        assert "EURUSD" in result
        assert len(result["EURUSD"]) == 1
        os.unlink(f.name)


def test_load_mt5_csvl():
    import json
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": "2024-01-15 10:00:00", "open": 1.1000, "high": 1.1005, "low": 1.0995, "close": 1.1002}) + "\n")
        f.write(json.dumps({"time": "2024-01-15 11:00:00", "open": 1.1002, "high": 1.1008, "low": 1.1000, "close": 1.1005}) + "\n")
        f.flush()
        result = load_mt5_csvl(f.name)
        assert len(result) == 2
        assert isinstance(result[0]["timestamp"], datetime)
        os.unlink(f.name)
