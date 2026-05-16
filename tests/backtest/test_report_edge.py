
import os
import tempfile
import pytest
from backtesting.report import ReportGenerator

def test_empty_trades_csv():
    r = ReportGenerator({"trades": []})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "trades.csv")
        r.to_csv(path)
        assert not os.path.exists(path) or os.path.getsize(path) == 0

def test_empty_trades_markdown():
    r = ReportGenerator({"summary": {"total_trades": 0}, "trades": []})
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.md")
        r.to_markdown(path)
        with open(path, "r") as f:
            content = f.read()
        assert "Total trades: 0" in content
