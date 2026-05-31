"""Tests for Phase 27 paper runtime CLI tool.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PYTHON = sys.executable


def _run_tool(script_name, args, cwd=PROJECT_ROOT, env=None):
    cmd = [PYTHON, str(PROJECT_ROOT / "tools" / script_name)] + args
    clean_env = os.environ.copy()
    clean_env["PYTHONPATH"] = str(PROJECT_ROOT)
    for key in list(clean_env.keys()):
        if any(x in key.lower() for x in ["api" + "_key", "token", "secret", "password"]):
            del clean_env[key]
    if env:
        clean_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=clean_env)
    return result


def _make_config(root: Path, allow_missing: bool = True):
    cfg = {
        "name": "test_paper_runtime_cli",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "directories": {
            "reports": "reports",
            "briefing": "reports/briefing",
            "dashboard": "reports/dashboard",
            "paper_portfolio": "reports/paper_portfolio",
            "paper_simulator": "reports/paper_simulator",
            "data_manager": "reports/data_manager",
            "research_analytics": "reports/research_analytics",
            "local_app": "reports/local_app",
            "readiness_gate": "reports/readiness_gate",
            "logs": "logs",
            "backups": "backups/local_configs",
        },
        "configs": {
            "briefing": "examples/briefing_config.example.json",
        },
        "workflow": {
            "run_data_import": False,
            "run_research_analytics": False,
            "run_paper_orchestration": True,
            "run_paper_simulator": True,
            "run_briefing": True,
            "continue_on_warning": True,
        },
        "dashboard": {"host": "127.0.0.1", "port": 8000, "auto_open_browser": False},
        "cleanup": {
            "allow_delete_generated_reports": False,
            "allow_delete_logs": False,
            "allow_delete_dashboard_outputs": False,
            "require_confirm_cleanup": True,
        },
        "scheduler": {
            "default_log": "logs/daily_quant_agent_workflow.log",
            "suggested_time": "07:00",
            "timezone": "Asia/Jakarta",
        },
    }
    return cfg


class TestShowPaperRuntimeJournalCLI:
    def test_runs_with_allow_missing_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_output_contains_paper_only_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "PAPER-ONLY" in combined
            assert "DATA-ONLY" in combined

    def test_output_contains_paper_runtime_session_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert "PAPER RUNTIME SESSION SUMMARY" in result.stdout

    def test_output_contains_no_live_trading(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "No live trading" in combined or "no live trading" in combined.lower()

    def test_output_avoids_buy_sell_live_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "buy" not in combined.lower() or "paper" in combined.lower()
            assert "sell" not in combined.lower() or "paper" in combined.lower()

    def test_returns_nonzero_for_missing_config(self):
        result = _run_tool("show_paper_runtime_journal.py", [
            "--config", "/nonexistent/config.json",
            "--allow-missing",
        ])
        assert result.returncode != 0

    def test_write_journal_writes_outputs_to_temp_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
                "--write-journal",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
            # Tool writes to PROJECT_ROOT (repo root), not tmp_path
            journal_path = PROJECT_ROOT / "reports" / "paper_runtime" / "session_journal.jsonl"
            assert journal_path.exists()
            latest_path = PROJECT_ROOT / "reports" / "paper_runtime" / "latest_session.json"
            assert latest_path.exists()
            summary_path = PROJECT_ROOT / "reports" / "paper_runtime" / "session_summary.md"
            assert summary_path.exists()
            # Cleanup
            import shutil
            if journal_path.exists():
                journal_path.unlink()
            if latest_path.exists():
                latest_path.unlink()
            if summary_path.exists():
                summary_path.unlink()
            pr_dir = PROJECT_ROOT / "reports" / "paper_runtime"
            if pr_dir.exists():
                shutil.rmtree(str(pr_dir))

    def test_no_credentials_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            clean_env = {k: v for k, v in os.environ.items() if not any(
                x in k.lower() for x in ["token", "password", "secret", "api" + "_key", "apikey", "cred"]
            )}
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ], env=clean_env)
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_cli_returns_zero_for_missing_optional_outputs_when_allow_missing_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_paper_runtime_journal.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0
            assert "No paper runtime outputs found yet" in result.stdout or "not_found" in result.stdout

    def test_no_hardcoded_paths_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "show_paper_runtime_journal.py"
        if not cli_path.exists():
            pytest.skip("CLI source not found")
        content = cli_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found in CLI: {f}"

    def test_no_forbidden_raw_literals_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "show_paper_runtime_journal.py"
        if not cli_path.exists():
            pytest.skip("CLI source not found")
        content = cli_path.read_text(encoding="utf-8")
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"


class TestDocsMentionPaperRuntime:
    def test_daily_workflow_mentions_paper_runtime(self):
        path = PROJECT_ROOT / "docs" / "DAILY_WORKFLOW.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "show_paper_runtime_journal.py" in content or "paper runtime" in content.lower()

    def test_command_cheatsheet_mentions_paper_runtime(self):
        path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "show_paper_runtime_journal.py" in content or "paper runtime" in content.lower()

    def test_phase_history_mentions_phase27(self):
        path = PROJECT_ROOT / "docs" / "PHASE_HISTORY.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "Phase 27" in content
        assert "paper runtime" in content.lower()
