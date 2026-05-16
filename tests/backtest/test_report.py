
import os
import tempfile
import pytest
from backtesting.report import ReportGenerator

def test_json_report():
    results = {"summary": {"trades": 5}, "trades": [{"pnl": 100}]}
    r = ReportGenerator(results)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.json")
        r.to_json(path)
        assert os.path.exists(path)

def test_csv_report():
    results = {"trades": [{"symbol": "EURUSD", "pnl": 100}, {"symbol": "GBPUSD", "pnl": -50}]}
    r = ReportGenerator(results)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "trades.csv")
        r.to_csv(path)
        assert os.path.exists(path)

def test_markdown_report():
    results = {"summary": {"total_trades": 2}, "trades": [{"symbol": "EURUSD", "direction": "buy", "entry_price": 1.1, "exit_price": 1.11, "pnl": 100}]}
    r = ReportGenerator(results)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.md")
        r.to_markdown(path)
        assert os.path.exists(path)
        with open(path, "r") as f:
            content = f.read()
        assert "Backtest Report" in content
        assert "EURUSD" in content
