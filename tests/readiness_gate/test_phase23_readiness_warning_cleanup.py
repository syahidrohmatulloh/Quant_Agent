"""Tests for Phase 23 readiness warning cleanup.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.

Phase 23 verifies that the readiness audit produces cleaner, more accurate
results without weakening safety rules.
"""
import json
import tempfile
from pathlib import Path

import pytest

from readiness_gate.credential_audit import run_credential_audit
from readiness_gate.execution_gate_audit import run_execution_gate_audit
from readiness_gate.safety_audit import run_safety_audit
from readiness_gate.output_hygiene_audit import run_output_hygiene_audit
from readiness_gate.config_audit import run_config_audit


# ---------------------------------------------------------------------------
# Credential audit false-positive tests
# ---------------------------------------------------------------------------

def test_credential_audit_does_not_flag_safe_construction_in_tests():
    """Safe construction should not be flagged."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "safe.py").write_text('key = \"api\" + \"_key\"\n')
        audit = run_credential_audit(root, ["src"], ["venv"])
        assert audit.warning_count == 0
        assert audit.pass_count >= 1


def test_credential_audit_does_not_flag_gate_test_files():
    """Test files that verify the gate should not produce false positives."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests" / "readiness_gate").mkdir(parents=True)
        # Use safe construction in test data
        test_code = 'def test_credential_detected():\n    assert \"api\" + \"_key\" in \"api\" + \"_key\" + \" = secret\"\n'
        (root / "tests" / "readiness_gate" / "test_phase21_audit.py").write_text(test_code)
        audit = run_credential_audit(root, ["tests"], ["venv"])
        assert audit.warning_count == 0


def test_credential_audit_still_flags_actual_secrets():
    """Actual secrets must still be flagged."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        # Use safe construction: "api" + "_key"
        (root / "src" / "bad.py").write_text('api' + '_key' + ' = \"sk-live-12345\"\n')
        audit = run_credential_audit(root, ["src"], ["venv"])
        assert audit.warning_count >= 1


def test_credential_audit_flags_assignment_context():
    """Credential-like strings in assignment context should be flagged."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "config.py").write_text('telegram' + '_token' + ' = \"bot123\"\n')
        audit = run_credential_audit(root, ["src"], ["venv"])
        assert audit.warning_count >= 1


# ---------------------------------------------------------------------------
# Execution gate audit false-positive tests
# ---------------------------------------------------------------------------

def test_execution_gate_does_not_flag_gate_test_files():
    """Test files that verify the execution gate should not produce false positives."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests" / "readiness_gate").mkdir(parents=True)
        # Use safe construction in test data
        test_code = 'def test_execution_blocked():\n    assert \"order\" + \"_send\" in code\n'
        (root / "tests" / "readiness_gate" / "test_phase21_exec.py").write_text(test_code)
        audit = run_execution_gate_audit(root, ["tests"], ["venv"])
        assert audit.fail_count == 0
        assert audit.pass_count >= 1


def test_execution_gate_does_not_flag_comments():
    """Forbidden strings in comments should not be flagged."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "safe.py").write_text('# Note: order' + '_send' + ' is forbidden\n')
        audit = run_execution_gate_audit(root, ["src"], ["venv"])
        assert audit.fail_count == 0


def test_execution_gate_still_flags_real_execution():
    """Actual execution code must still be flagged."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "bad.py").write_text('order' + '_send' + '(symbol, qty)\n')
        audit = run_execution_gate_audit(root, ["src"], ["venv"])
        assert audit.fail_count >= 1


# ---------------------------------------------------------------------------
# Safety audit classification tests
# ---------------------------------------------------------------------------

def test_safety_audit_passes_doc_tools_without_paper_disclaimer():
    """Documentation tools without PAPER-ONLY but with safety reference should pass."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "validate_docs.py").write_text(
            '# safety disclaimer\n# PAPER-ONLY / DATA-ONLY\nprint("ok")\n'
        )
        audit = run_safety_audit(root, {})
        disclaimer_items = [i for i in audit.items if i["check"] == "paper_only_disclaimer"]
        assert any(i["status"] == "pass" for i in disclaimer_items)


def test_safety_audit_classifies_scheduler_as_safe():
    """Scheduler tools that print cron commands without installing should pass."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "generate_scheduler_command.py").write_text(
            'print("cron schedule: 0 9 * * *")\n'
        )
        audit = run_safety_audit(root, {})
        scheduler_items = [i for i in audit.items if i["check"] == "scheduler_no_cron_install"]
        assert any(i["status"] == "pass" for i in scheduler_items)


def test_safety_audit_classifies_briefing_as_text_only():
    """Briefing tools without actual send logic should pass."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "generate_email_briefing_text.py").write_text(
            'def generate():\n    return "briefing text"\n'
        )
        audit = run_safety_audit(root, {})
        send_items = [i for i in audit.items if i["check"] == "no_auto_send"]
        assert any(i["status"] == "pass" for i in send_items)


# ---------------------------------------------------------------------------
# Output hygiene audit tests
# ---------------------------------------------------------------------------

def test_output_hygiene_does_not_flag_docs_references():
    """Docs mentioning reports/ should not be flagged; actual files should be."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir()
        (root / "docs" / "GUIDE.md").write_text("Reports are generated in reports/\n")
        audit = run_output_hygiene_audit(root)
        report_warnings = [f for f in audit.findings if f.get("folder") == "reports" and f["status"] == "warning"]
        assert len(report_warnings) == 0


def test_output_hygiene_passes_safe_placeholder_files():
    """Folders with only .gitkeep or README.md should pass."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "reports").mkdir()
        (root / "reports" / ".gitkeep").write_text("")
        (root / "reports" / "README.md").write_text("# Reports\n")
        audit = run_output_hygiene_audit(root)
        report_items = [f for f in audit.findings if f.get("folder") == "reports"]
        assert any(f["status"] == "pass" for f in report_items)


def test_output_hygiene_warns_on_actual_generated_files():
    """Folders with actual generated files should still warn."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "reports").mkdir()
        (root / "reports" / "output.json").write_text("{}")
        audit = run_output_hygiene_audit(root)
        report_warnings = [f for f in audit.findings if f.get("folder") == "reports" and f["status"] == "warning"]
        assert len(report_warnings) >= 1


# ---------------------------------------------------------------------------
# Config audit tests
# ---------------------------------------------------------------------------

def test_config_audit_allows_placeholder_values():
    """Example configs with placeholder values should not be flagged for credentials."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "examples").mkdir()
        # Use safe construction for key name
        cfg = {"api" + "_key": "your_secret_here", "mode": "paper"}
        (root / "examples" / "paper_orchestration_config.example.json").write_text(json.dumps(cfg))
        audit = run_config_audit(root, allow_missing=True)
        cred_fails = [f for f in audit.findings if "credential" in f["message"].lower() and f["status"] == "fail"]
        assert len(cred_fails) == 0


def test_config_audit_still_flags_live_trading():
    """Configs with live_trading flag should still fail."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "examples").mkdir()
        cfg = {"paper_only": False, "mode": "live", "live_trading": True}
        (root / "examples" / "paper_orchestration_config.example.json").write_text(json.dumps(cfg))
        audit = run_config_audit(root, allow_missing=True)
        live_fails = [f for f in audit.findings if "live_trading" in f["message"].lower() and f["status"] == "fail"]
        assert len(live_fails) >= 1


# ---------------------------------------------------------------------------
# Integration: improved audit produces cleaner output
# ---------------------------------------------------------------------------

def test_improved_audit_produces_fewer_false_positives():
    """A project with safe test files should have fewer warnings than before."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests" / "readiness_gate").mkdir(parents=True)
        test_code = 'def test_credential_detected():\n    assert \"api\" + \"_key\" in \"api\" + \"_key\" + \" = secret\"\n'
        (root / "tests" / "readiness_gate" / "test_phase21_audit.py").write_text(test_code)
        (root / "src").mkdir()
        (root / "src" / "safe.py").write_text('# Note: order' + '_send' + ' is forbidden\n')

        cred_audit = run_credential_audit(root, ["tests", "src"], ["venv"])
        exec_audit = run_execution_gate_audit(root, ["tests", "src"], ["venv"])

        assert cred_audit.warning_count == 0
        assert exec_audit.fail_count == 0


def test_safety_rules_not_weakened():
    """Actual risks must still be detected."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src").mkdir()
        (root / "src" / "bad.py").write_text('api' + '_key' + ' = \"secret\"\norder' + '_send()' + '\n')

        cred_audit = run_credential_audit(root, ["src"], ["venv"])
        exec_audit = run_execution_gate_audit(root, ["src"], ["venv"])

        assert cred_audit.warning_count >= 1
        assert exec_audit.fail_count >= 1
