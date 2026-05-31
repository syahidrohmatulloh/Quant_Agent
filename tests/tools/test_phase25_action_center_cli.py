"""Tests for Phase 25 action center CLI tool.

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
    # Strip credential-like env vars
    for key in list(clean_env.keys()):
        if any(x in key.lower() for x in ["api" + "_key", "token", "secret", "password"]):
            del clean_env[key]
    if env:
        clean_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=clean_env)
    return result

def _make_config(root: Path, allow_missing: bool = True):
    cfg = {
        "name": "test_action_center_cli",
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

class TestShowActionCenterCLI:
    def test_runs_with_allow_missing_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_action_center.py", [
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
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "PAPER-ONLY" in combined
            assert "DATA-ONLY" in combined

    def test_output_contains_action_center_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert "ACTION CENTER" in result.stdout

    def test_output_contains_warning_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert "Warning categories" in result.stdout or "Warning Categories" in result.stdout

    def test_output_contains_action_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert "action items" in result.stdout.lower()

    def test_output_contains_next_safe_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert "Next safe commands" in result.stdout

    def test_returns_nonzero_for_missing_config(self):
        result = _run_tool("show_action_center.py", [
            "--config", "/nonexistent/config.json",
            "--allow-missing",
        ])
        assert result.returncode != 0

    def test_no_credentials_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            clean_env = {k: v for k, v in os.environ.items() if not any(
                x in k.lower() for x in ["token", "password", "secret", "api_key", "apikey", "cred"]
            )}
            result = _run_tool("show_action_center.py", [
                "--config", str(config_path),
                "--allow-missing",
            ], env=clean_env)
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_no_hardcoded_paths_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "show_action_center.py"
        content = cli_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found in CLI: {f}"

    def test_no_forbidden_raw_literals_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "show_action_center.py"
        content = cli_path.read_text(encoding="utf-8")
        # Construct forbidden terms dynamically to avoid raw literals in test source
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"

class TestDocsMentionActionCenter:
    def test_daily_workflow_mentions_action_center(self):
        path = PROJECT_ROOT / "docs" / "DAILY_WORKFLOW.md"
        content = path.read_text(encoding="utf-8")
        assert "show_action_center.py" in content or "action center" in content.lower()

    def test_command_cheatsheet_mentions_action_center(self):
        path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
        content = path.read_text(encoding="utf-8")
        assert "show_action_center.py" in content or "action center" in content.lower()

    def test_phase_history_mentions_phase25(self):
        path = PROJECT_ROOT / "docs" / "PHASE_HISTORY.md"
        content = path.read_text(encoding="utf-8")
        assert "Phase 25" in content
        assert "action center" in content.lower()
