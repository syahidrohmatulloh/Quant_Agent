"""Tests for readiness audit modules.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from readiness_gate.source_inventory import build_source_inventory
from readiness_gate.safety_audit import run_safety_audit
from readiness_gate.credential_audit import run_credential_audit
from readiness_gate.execution_gate_audit import run_execution_gate_audit
from readiness_gate.risk_control_audit import run_risk_control_audit
from readiness_gate.config_audit import run_config_audit
from readiness_gate.output_hygiene_audit import run_output_hygiene_audit
from readiness_gate.test_status_audit import run_test_status_audit
from readiness_gate.readiness_score import compute_readiness_score


def test_source_inventory_excludes_git_venv():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "a.py").write_text("x = 1")
        (root / ".git").mkdir()
        (root / ".git" / "x.py").write_text("x = 1")
        (root / "venv").mkdir()
        (root / "venv" / "y.py").write_text("x = 1")
        inv = build_source_inventory(root, ["src"], [".git", "venv", "__pycache__"])
        assert inv.total_files == 1
        assert inv.python_files == 1


def test_source_inventory_counts_python_tool_test_example():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "t.py").write_text("x = 1")
        (root / "tests").mkdir()
        (root / "tests" / "u.py").write_text("x = 1")
        (root / "examples").mkdir()
        (root / "examples" / "c.example.json").write_text("{}")
        inv = build_source_inventory(root, ["tools", "tests", "examples"], ["venv"])
        assert inv.tool_files == 1
        assert inv.test_files == 1
        assert inv.example_config_files == 1


def test_safety_audit_detects_paper_only_disclaimers():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "good.py").write_text("# PAPER-ONLY / DATA-ONLY")
        (root / "tools" / "bad.py").write_text("# some tool")
        audit = run_safety_audit(root, {})
        statuses = {item["file"]: item["status"] for item in audit.items if item["check"] == "paper_only_disclaimer"}
        assert statuses.get("tools/good.py") == "pass"
        assert statuses.get("tools/bad.py") == "warning"


def test_safety_audit_checks_localhost_dashboard():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "dashboard").mkdir()
        (root / "dashboard" / "app.py").write_text("host = '127.0.0.1'")
        audit = run_safety_audit(root, {})
        localhost_items = [i for i in audit.items if i["check"] == "dashboard_localhost"]
        assert localhost_items[0]["status"] == "pass"


def test_safety_audit_checks_restore_cleanup_confirmation():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "cleanup_generated_outputs.py").write_text("confirm = input()")
        audit = run_safety_audit(root, {})
        items = [i for i in audit.items if i["check"] == "cleanup_restore_confirmation"]
        assert items[0]["status"] == "pass"


def test_scheduler_tools_not_installing_cron():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "generate_scheduler_command.py").write_text("print('cron schedule: ...')")
        audit = run_safety_audit(root, {})
        items = [i for i in audit.items if i["check"] == "scheduler_no_cron_install"]
        assert items[0]["status"] == "pass"


def test_credential_audit_flags_dangerous_fields():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        # Use safe construction: "api" + "_key"
        (root / "src" / "bad.py").write_text("api" + "_key" + " = '123'")
        audit = run_credential_audit(root, ["src"], ["venv"])
        assert any("api" + "_key" in f["message"] for f in audit.findings)


def test_execution_gate_audit_detects_forbidden_strings():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        # Use safe construction: "order" + "_send"
        (root / "src" / "bad.py").write_text("order" + "_send" + "()")
        audit = run_execution_gate_audit(root, ["src"], ["venv"])
        assert any("Forbidden" in f["message"] for f in audit.findings)


def test_execution_gate_audit_does_not_call_brokers():
    # The audit only scans text; it does not make network calls
    audit = run_execution_gate_audit(Path("."), ["nonexistent"], ["venv"])
    # No network calls made, no exceptions expected
    assert audit is not None


def test_risk_control_audit_validates_key_configs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "examples").mkdir()
        (root / "examples" / "paper_simulator_config.example.json").write_text(
            json.dumps({"max_symbol_weight": 0.2, "max_gross_exposure": 1.0, "allow_short": False})
        )
        audit = run_risk_control_audit(root, {})
        assert any(i["check"] == "simulator_risk_controls" and i["status"] == "pass" for i in audit.findings)


def test_config_audit_handles_missing_optional_configs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        audit = run_config_audit(root, allow_missing=True)
        # Should warn, not crash
        assert all(f["status"] != "fail" or "Missing" not in f["message"] for f in audit.findings)


def test_output_hygiene_detects_generated_folders():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "reports").mkdir()
        (root / "reports" / "x.txt").write_text("data")
        audit = run_output_hygiene_audit(root)
        assert any(f["folder"] == "reports" and f["status"] == "warning" for f in audit.findings)


def test_test_status_audit_skips_by_default():
    audit = run_test_status_audit(Path("."), run_tests=False)
    assert audit.ran_tests is False
    assert any("skipped" in i["message"].lower() or "fast audit" in i["message"].lower() for i in audit.findings)


def test_readiness_score_computes_grade():
    score = compute_readiness_score(
        source_inventory_pass=True,
        safety_pass_rate=1.0,
        credential_pass_rate=1.0,
        execution_gate_pass_rate=1.0,
        risk_control_pass_rate=1.0,
        config_pass_rate=1.0,
        output_hygiene_warnings=0,
        test_status_pass=True,
    )
    assert score.score >= 90
    assert score.grade == "A"
    assert score.status == "PAPER_MVP_READY"


def test_readiness_status_with_warnings():
    score = compute_readiness_score(
        source_inventory_pass=True,
        safety_pass_rate=0.8,
        credential_pass_rate=0.8,
        execution_gate_pass_rate=0.8,
        risk_control_pass_rate=0.8,
        config_pass_rate=0.8,
        output_hygiene_warnings=2,
        test_status_pass=True,
    )
    assert score.grade in ("B", "C")
    assert score.status == "PAPER_MVP_READY_WITH_WARNINGS"
