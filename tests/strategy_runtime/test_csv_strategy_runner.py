"""
Test strategy runner on CSV data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import csv
import tempfile
from strategy_runtime.csv_strategy_runner import run_strategy_on_csv, run_backtest_on_csv


def _make_csv(n=30, trend="up"):
    rows = []
    price = 1.1000
    for i in range(n):
        delta = 0.001 if trend == "up" else (-0.001 if trend == "down" else 0.0)
        o = price
        c = price + delta
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        rows.append({
            "time": f"2024.01.{15 + i//24:02d} {i%24:02d}:00",
            "open": str(o), "high": str(h), "low": str(l), "close": str(c),
            "tick_volume": "1000"
        })
        price = c
    return rows


def _write_csv(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_run_strategy_ma_crossover():
    rows = _make_csv(30, "up")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = run_strategy_on_csv(f.name, "ma_crossover", symbol="EURUSD", timeframe="H1",
                                      strategy_params={"fast": 3, "slow": 10})
        assert result["status"] == "ok"
        assert result["strategy"] == "ma_crossover"
        assert result["latest_signal"] is not None
        os.unlink(f.name)


def test_run_strategy_time_series_momentum():
    rows = _make_csv(30, "down")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = run_strategy_on_csv(f.name, "time_series_momentum", symbol="EURUSD", timeframe="H1",
                                      strategy_params={"lookback": 5, "threshold": 0.001})
        assert result["status"] == "ok"
        assert result["latest_signal"] is not None
        os.unlink(f.name)


def test_run_backtest_ma_crossover():
    rows = _make_csv(50, "up")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = run_backtest_on_csv(f.name, "ma_crossover", symbol="EURUSD", timeframe="H1",
                                      strategy_params={"fast": 3, "slow": 10})
        assert result["status"] == "ok"
        assert "backtest" in result
        bt = result["backtest"]
        assert "total_return" in bt
        assert "max_drawdown" in bt
        assert "volatility" in bt
        os.unlink(f.name)


def test_run_strategy_validation_fail():
    rows = [
        {"time": "2024.01.15 10:00", "open": "1.1000", "high": "1.1005", "close": "1.1002"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "close"])
        result = run_strategy_on_csv(f.name, "ma_crossover", symbol="EURUSD", timeframe="H1")
        assert result["status"] == "validation_failed"
        os.unlink(f.name)
