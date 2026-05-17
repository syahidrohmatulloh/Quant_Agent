"""
Test decision report generation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import tempfile
from pathlib import Path
from experiment_manager.decision_report import generate_markdown_report, generate_json_result


def test_report_includes_paper_only_disclaimer():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "report.md")
        report = generate_markdown_report(
            experiment_name="test",
            config={"symbols": [], "strategies": []},
            symbol_results=[],
            validation_summary={"valid": True, "errors": [], "warnings": []},
            output_path=out_path,
        )
        assert "PAPER-ONLY" in report
        assert "not financial advice" in report.lower()
        assert Path(out_path).exists()


def test_json_dashboard_export_shape():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "result.json")
        result = generate_json_result(
            experiment_name="test",
            config={"symbols": [], "strategies": []},
            symbol_results=[],
            validation_summary={"valid": True, "errors": [], "warnings": []},
            output_path=out_path,
        )
        assert result["experiment_name"] == "test"
        assert result["paper_only"] is True
        assert result["data_only"] is True
        assert "symbols" in result
        assert Path(out_path).exists()
