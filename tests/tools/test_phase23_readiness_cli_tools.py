"""Tests for Phase 23 readiness CLI tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run_tool(tool_name, extra_args=None, cwd=None):
    cmd = [sys.executable, f"tools/{tool_name}"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result


def test_check_paper_only_safety_cli_still_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY / DATA-ONLY\n")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            for f in src_tools.glob("check_paper_only_safety.py"):
                shutil.copy(f, root / "tools" / f.name)

        src_rg = Path(__file__).resolve().parents[2] / "readiness_gate"
        if src_rg.exists():
            shutil.copytree(src_rg, root / "readiness_gate", dirs_exist_ok=True)

        (root / "examples").mkdir()
        import json
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "project_root": ".",
            "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv"]},
            "audit_rules": {}, "outputs": {}
        }
        (root / "examples" / "config.json").write_text(json.dumps(cfg))

        result = _run_tool("check_paper_only_safety.py", ["--config", "examples/config.json"], cwd=root)
        assert result.returncode == 0


def test_check_credential_exposure_cli_reduces_false_positives():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "safe.py").write_text('key = \"api\" + \"_key\"\n')

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            for f in src_tools.glob("check_credential_exposure.py"):
                shutil.copy(f, root / "tools" / f.name)

        src_rg = Path(__file__).resolve().parents[2] / "readiness_gate"
        if src_rg.exists():
            shutil.copytree(src_rg, root / "readiness_gate", dirs_exist_ok=True)

        (root / "examples").mkdir()
        import json
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "project_root": ".",
            "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv"]},
            "audit_rules": {}, "outputs": {}
        }
        (root / "examples" / "config.json").write_text(json.dumps(cfg))

        result = _run_tool("check_credential_exposure.py", ["--config", "examples/config.json"], cwd=root)
        assert result.returncode == 0
        assert "0 warning" in result.stdout or "pass" in result.stdout.lower()


def test_check_execution_gate_cli_reduces_false_positives():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "safe.py").write_text('# order' + '_send' + ' is forbidden\n')

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            for f in src_tools.glob("check_execution_gate.py"):
                shutil.copy(f, root / "tools" / f.name)

        src_rg = Path(__file__).resolve().parents[2] / "readiness_gate"
        if src_rg.exists():
            shutil.copytree(src_rg, root / "readiness_gate", dirs_exist_ok=True)

        (root / "examples").mkdir()
        import json
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "project_root": ".",
            "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv"]},
            "audit_rules": {}, "outputs": {}
        }
        (root / "examples" / "config.json").write_text(json.dumps(cfg))

        result = _run_tool("check_execution_gate.py", ["--config", "examples/config.json"], cwd=root)
        assert result.returncode == 0


def test_run_readiness_audit_cli_still_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tools").mkdir()
        (root / "tools" / "dummy.py").write_text("# PAPER-ONLY / DATA-ONLY\n")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            for f in src_tools.glob("run_readiness_audit.py"):
                shutil.copy(f, root / "tools" / f.name)

        src_rg = Path(__file__).resolve().parents[2] / "readiness_gate"
        if src_rg.exists():
            shutil.copytree(src_rg, root / "readiness_gate", dirs_exist_ok=True)

        (root / "examples").mkdir()
        import json
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "project_root": ".",
            "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv"]},
            "audit_rules": {},
            "outputs": {
                "readiness_report_md": "reports/readiness_gate/readiness_report.md",
                "readiness_report_json": "reports/readiness_gate/readiness_report.json",
                "dashboard_json": "reports/dashboard/readiness_gate/latest.json",
                "readiness_log": "reports/readiness_gate/readiness_log.jsonl"
            }
        }
        (root / "examples" / "config.json").write_text(json.dumps(cfg))

        result = _run_tool("run_readiness_audit.py", ["--config", "examples/config.json", "--allow-missing"], cwd=root)
        assert result.returncode in (0, 1)
        assert "Traceback" not in result.stderr
        assert "Readiness score" in result.stdout
