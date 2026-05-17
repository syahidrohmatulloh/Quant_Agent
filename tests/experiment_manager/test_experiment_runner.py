"""
Test experiment runner with temp CSV fixtures.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import csv
import tempfile
from pathlib import Path
from experiment_manager.experiment_runner import run_experiment


def _make_csv(n=50, trend="up"):
    rows = []
    price = 1.1000
    for i in range(n):
        delta = 0.001 if trend == "up" else (-0.001 if trend == "down" else 0.0)
        o = price
        c = price + delta
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        rows.append({
            "time": "2024.01." + str(15 + i//24).zfill(2) + " " + str(i%24).zfill(2) + ":00",
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


def test_experiment_runner_with_temp_csv():
    rows = _make_csv(50, "up")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, rows, ["time", "open", "high", "low", "close", "tick_volume"])

        config = {
            "name": "test_run",
            "paper_only": True,
            "data_only": True,
            "symbols": [
                {"symbol": "EURUSD", "timeframe": "H1", "csv": csv_path}
            ],
            "strategies": [
                {"name": "ma_crossover", "params": {"fast": 3, "slow": 10}}
            ],
            "backtest": True,
            "consensus": {"method": "majority_vote", "minimum_agreement": 0.6},
        }

        result = run_experiment(
            config=config,
            config_path=os.path.join(tmpdir, "config.json"),
            output_dir=os.path.join(tmpdir, "reports"),
            dashboard_dir=os.path.join(tmpdir, "dashboard"),
            history_dir=os.path.join(tmpdir, "history"),
        )

        assert "run_id" in result
        assert result["paper_only"] is True
        assert result["data_only"] is True
        assert Path(result["markdown_path"]).exists()
        assert Path(result["json_path"]).exists()
        assert Path(result["dashboard_path"]).exists()
        assert Path(result["history_file"]).exists()

        sym_results = result["symbol_results"]
        assert len(sym_results) == 1
        assert sym_results[0]["symbol"] == "EURUSD"
        assert "consensus" in sym_results[0]
        assert "comparison" in sym_results[0]
