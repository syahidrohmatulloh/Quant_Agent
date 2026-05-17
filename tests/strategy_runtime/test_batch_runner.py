"""
Test batch runner with multiple strategies.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import csv
import tempfile
from strategy_runtime.batch_runner import run_batch


def _make_csv(n=30):
    rows = []
    price = 1.1000
    for i in range(n):
        o = price
        c = price + 0.001
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


def test_batch_multiple_strategies():
    rows = _make_csv(30)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = run_batch(f.name, ["ma_crossover", "time_series_momentum"],
                           symbol="EURUSD", timeframe="H1")
        assert result["status"] == "ok"
        assert len(result["signals"]) == 2
        os.unlink(f.name)
