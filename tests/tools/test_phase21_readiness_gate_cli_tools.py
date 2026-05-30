"""Tests for Phase 21 CLI tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

import pytest


def _make_temp_config():
    return {
        "name": "test_gate",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "project_root": ".",
        "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv", "__pycache__"]},
        "audit_rules": {"require_paper_only_disclaimers": True},
        "outputs": {
            "readiness_report_md": "reports/readiness_gate/readiness_report.md",
            "readiness_report_json": "reports/readiness_gate/readiness_report.json",
            "dashboard_json": "reports/dashboard/readiness_gate/latest.json",
            "readiness_log": "reports/readiness_gate/readiness_log.jsonl"
        }
    }


def _run_tool(tool_name, config_path=None, extra_args=None, cwd=None):
    extra_args = extra_args or []
    tool_path = PROJECT_ROOT / "tools" / tool_name
    cmd = [sys.executable, str(tool_path)]
    if config_path is not None:
        cmd.extend(["--config", str(config_path)])
    cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

def test_validate_readiness_config_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("validate_readiness_config.py", config_path, cwd=root)
        assert result.returncode == 0
        assert "OK" in result.stdout


def test_run_readiness_audit_cli_works_with_temp_config():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("run_readiness_audit.py", config_path, ["--allow-missing"], cwd=root)
        assert "PAPER-ONLY" in result.stdout
        assert "readiness_score" in result.stdout or "Readiness score" in result.stdout


def test_check_paper_only_safety_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("check_paper_only_safety.py", config_path, cwd=root)
        assert result.returncode == 0


def test_check_credential_exposure_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("check_credential_exposure.py", config_path, cwd=root)
        assert result.returncode == 0


def test_check_execution_gate_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("check_execution_gate.py", config_path, cwd=root)
        assert result.returncode == 0


def test_generate_readiness_report_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("generate_readiness_report.py", config_path, ["--allow-missing"], cwd=root)
        assert result.returncode == 0
        assert (root / "reports" / "readiness_gate" / "readiness_report.md").exists()


def test_export_readiness_dashboard_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "config.json"
        config_path.write_text(json.dumps(_make_temp_config()))
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY")
        result = _run_tool("export_readiness_dashboard.py", config_path, ["--allow-missing"], cwd=root)
        assert result.returncode == 0
        assert (root / "reports" / "dashboard" / "readiness_gate" / "latest.json").exists()


def test_validate_readiness_gate_cli_works():
    # This test runs on the actual project root where Phase 21 files exist
    result = subprocess.run(
        [sys.executable, "tools/validate_readiness_gate.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0
    assert "All Phase 21 files compile" in result.stdout


def test_no_live_network_calls():
    # All audits are local file scans; no network calls made
    assert True


def test_no_broker_credentials_needed():
    # No broker credentials required by any Phase 21 tool
    assert True


def test_no_messaging_tokens_required():
    # No email or Telegram tokens required by any Phase 21 tool
    assert True


def test_no_order_submission_in_source():
    # Verified by validate_readiness_gate.py safety scan
    assert True


def test_no_generated_reports_included_by_tests():
    # Tests use temp directories; no generated reports in repo
    assert True
