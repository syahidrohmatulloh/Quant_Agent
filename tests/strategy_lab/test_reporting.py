import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Test report generation includes disclaimer.
"""
import os
import pytest
from strategy_lab.reporting import StrategyReportGenerator, PAPER_DISCLAIMER


def test_report_json(tmp_path):
    result = {"total_return": 0.05}
    config = {"strategy": "test"}
    gen = StrategyReportGenerator(result, config, output_dir=str(tmp_path))
    path = gen.to_json("report.json")
    assert os.path.exists(path)
    import json
    with open(path) as f:
        payload = json.load(f)
    assert PAPER_DISCLAIMER in payload["disclaimer"]


def test_report_markdown(tmp_path):
    result = {"total_return": 0.05}
    config = {"strategy": "test"}
    gen = StrategyReportGenerator(result, config, output_dir=str(tmp_path))
    path = gen.to_markdown("report.md")
    assert os.path.exists(path)
    with open(path) as f:
        text = f.read()
    assert "DISCLAIMER" in text
