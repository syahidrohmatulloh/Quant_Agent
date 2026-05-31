"""Tests for Phase 24 operator CLI tools.

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


def _run_cli(args, cwd=None, env=None):
    cmd = [sys.executable] + args
    result = subprocess.run(
        cmd,
        cwd=cwd or str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def _make_local_config(tmp: Path) -> Path:
    config = {
        "name": "test_quant_agent_local_app",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "project_root": ".",
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
            "backups": "backups",
        },
        "configs": {
            "briefing": "examples/briefing_config.example.json",
            "paper_simulator": "examples/paper_simulator_config.example.json",
            "paper_orchestration": "examples/paper_orchestration_config.example.json",
            "research_analytics": "examples/research_analytics_config.example.json",
            "data_import": "examples/market_data_import_config.example.json",
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
    config_path = tmp / "local_app_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config_path


class TestRunOperatorDayCLI:
    def test_runs_with_allow_missing_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_output_contains_paper_only_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "PAPER-ONLY" in combined
            assert "DATA-ONLY" in combined

    def test_output_contains_no_live_trading(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "No live trading" in combined or "no live trading" in combined.lower()

    def test_output_contains_no_order_submission(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "order" in combined.lower()
            assert "submission" in combined.lower() or "submit" in combined.lower()

    def test_output_contains_next_safe_dashboard_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "Next safe commands" in combined
            assert "run_local_dashboard" in combined

    def test_returns_nonzero_for_missing_config(self):
        result = _run_cli([
            "tools/run_operator_day.py",
            "--config", "/nonexistent/config.json",
            "--allow-missing",
        ])
        assert result.returncode != 0
        assert "BLOCKED" in result.stdout or "BLOCKED" in result.stderr

    def test_no_credentials_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            clean_env = {k: v for k, v in os.environ.items() if not any(
                x in k.lower() for x in ["token", "password", "secret", "api_key", "apikey", "cred"]
            )}
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ], env=clean_env)
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_generated_paths_are_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = _make_local_config(tmp_path)
            result = _run_cli([
                "tools/run_operator_day.py",
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0
            op_status = PROJECT_ROOT / "reports" / "local_app" / "operator_status.json"
            assert op_status.exists()
            data = json.loads(op_status.read_text(encoding="utf-8"))
            assert data.get("paper_only") is True
            assert data.get("data_only") is True

    def test_no_hardcoded_paths_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "run_operator_day.py"
        content = cli_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found in CLI: {f}"

    def test_no_forbidden_raw_literals_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "run_operator_day.py"
        content = cli_path.read_text(encoding="utf-8")
        raw_forbidden = ["order_send", "execute_order", "place_order", "submit_order"]
        for term in raw_forbidden:
            assert term not in content, f"Forbidden raw literal found: {term}"


class TestShowLocalAppStatusCLI:
    def test_still_works_with_example_config(self):
        example_config = PROJECT_ROOT / "examples" / "local_app_config.example.json"
        if not example_config.exists():
            pytest.skip("Example config not found")
        result = _run_cli([
            "tools/show_local_app_status.py",
            "--config", str(example_config),
        ])
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
        combined = result.stdout + result.stderr
        assert "PAPER-ONLY" in combined
        assert "DATA-ONLY" in combined

    def test_contains_safety_mode_section(self):
        example_config = PROJECT_ROOT / "examples" / "local_app_config.example.json"
        if not example_config.exists():
            pytest.skip("Example config not found")
        result = _run_cli([
            "tools/show_local_app_status.py",
            "--config", str(example_config),
        ])
        combined = result.stdout + result.stderr
        assert "Safety Mode" in combined

    def test_contains_local_outputs_section(self):
        example_config = PROJECT_ROOT / "examples" / "local_app_config.example.json"
        if not example_config.exists():
            pytest.skip("Example config not found")
        result = _run_cli([
            "tools/show_local_app_status.py",
            "--config", str(example_config),
        ])
        combined = result.stdout + result.stderr
        assert "Local Outputs" in combined

    def test_contains_readiness_section(self):
        example_config = PROJECT_ROOT / "examples" / "local_app_config.example.json"
        if not example_config.exists():
            pytest.skip("Example config not found")
        result = _run_cli([
            "tools/show_local_app_status.py",
            "--config", str(example_config),
        ])
        combined = result.stdout + result.stderr
        assert "Readiness" in combined

    def test_contains_next_safe_commands_section(self):
        example_config = PROJECT_ROOT / "examples" / "local_app_config.example.json"
        if not example_config.exists():
            pytest.skip("Example config not found")
        result = _run_cli([
            "tools/show_local_app_status.py",
            "--config", str(example_config),
        ])
        combined = result.stdout + result.stderr
        assert "Next Safe Commands" in combined


class TestDocsMentionOperatorCommand:
    def test_daily_workflow_mentions_operator(self):
        path = PROJECT_ROOT / "docs" / "DAILY_WORKFLOW.md"
        content = path.read_text(encoding="utf-8")
        assert "run_operator_day.py" in content
        assert "paper-only" in content.lower()
        assert "data-only" in content.lower()

    def test_command_cheatsheet_mentions_operator(self):
        path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
        content = path.read_text(encoding="utf-8")
        assert "run_operator_day.py" in content

    def test_phase_history_mentions_phase24(self):
        path = PROJECT_ROOT / "docs" / "PHASE_HISTORY.md"
        content = path.read_text(encoding="utf-8")
        assert "Phase 24" in content
        assert "operator" in content.lower()


class TestNoGeneratedReportsInTests:
    def test_no_reports_directory_in_test_file(self):
        test_path = Path(__file__)
        content = test_path.read_text(encoding="utf-8")
        assert "reports/" not in content or "tmp_path" in content
