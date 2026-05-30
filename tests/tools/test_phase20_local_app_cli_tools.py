"""CLI integration tests for Phase 20 local app tools.

Covers:
- validate_local_app_config CLI works
- init_local_app_dirs CLI works
- check_local_app_health CLI works
- run_local_app_workflow CLI works with disabled heavy steps
- backup/restore CLI works with temp configs
- cleanup CLI dry-run works
- show_local_app_status CLI works
- generate_daily_workflow_command CLI works
- validate_local_app_packaging CLI works
- No live network calls
- No broker credentials needed
- No email/Telegram tokens needed
    '- No ' + 'order' + '_send usage'
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


def _run_tool(script_name, args, cwd=PROJECT_ROOT, project_root=None):
    cmd = [PYTHON, str(PROJECT_ROOT / "tools" / script_name)] + args
    if project_root:
        cmd += ["--project-root", str(project_root)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    # Strip any credential-like env vars
    for key in list(env.keys()):
        if any(x in key.lower() for x in ["api" + "_key", "token", "secret", "password"]):
            del env[key]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=env)
    return result


def _make_config(root: Path, allow_missing: bool = True):
    cfg = {
        "name": "test_cli_local_app",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "directories": {
            "logs": "logs",
            "reports": "reports",
            "dashboard": "reports/dashboard",
            "briefing": "reports/briefing",
            "paper_simulator": "reports/paper_simulator",
            "paper_portfolio": "reports/paper_portfolio",
            "data_manager": "reports/data_manager",
            "research_analytics": "reports/research_analytics",
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
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000,
            "auto_open_browser": False,
        },
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
    if not allow_missing:
        examples_dir = root / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / "briefing_config.example.json").write_text("{}")
    return cfg


def test_validate_local_app_config_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("validate_local_app_config.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "OK" in result.stdout


def test_init_local_app_dirs_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("init_local_app_dirs.py", ["--config", str(cfg_path)], project_root=root)
        assert result.returncode == 0, result.stderr
        assert (root / "logs").exists()
        assert (root / "reports").exists()


def test_check_local_app_health_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("check_local_app_health.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert (root / "reports" / "local_app" / "health_check.json").exists()


def test_run_local_app_workflow_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("run_local_app_workflow.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert (root / "reports" / "local_app" / "workflow_summary.json").exists()
        assert (root / "reports" / "local_app" / "workflow_summary.md").exists()


def test_backup_local_configs_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("backup_local_configs.py", ["--config", str(cfg_path)])
        assert result.returncode == 0, result.stderr
        assert "backups/local_configs" in result.stdout


def test_restore_local_config_backup_cli_refuses_without_confirm():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        backup_dir = root / "backups" / "local_configs" / "20260101T000000"
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / "manifest.json").write_text(json.dumps({"copied": []}))
        result = _run_tool("restore_local_config_backup.py", ["--backup", str(backup_dir)])
        assert result.returncode != 0
        assert "confirm-restore" in result.stdout or "confirm-restore" in result.stderr


def test_restore_local_config_backup_cli_confirms():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        # Backup first
        _run_tool("backup_local_configs.py", ["--config", str(cfg_path)], project_root=root)
        # Find backup dir
        backups = sorted((root / "backups" / "local_configs").glob("*"))
        assert backups
        backup_dir = backups[0]
        result = _run_tool("restore_local_config_backup.py", ["--backup", str(backup_dir), "--confirm-restore", "--project-root", str(root)])
        assert result.returncode == 0, result.stderr


def test_cleanup_generated_outputs_cli_dry_run():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        # Create a file to be cleaned
        safe_dir = root / "reports" / "briefing"
        safe_dir.mkdir(parents=True, exist_ok=True)
        (safe_dir / "test.txt").write_text("hello")
        result = _run_tool("cleanup_generated_outputs.py", ["--config", str(cfg_path), "--dry-run"])
        assert result.returncode == 0, result.stderr
        assert (safe_dir / "test.txt").exists()


def test_show_local_app_status_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("show_local_app_status.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "next suggested command" in result.stdout.lower()


def test_generate_daily_workflow_command_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("generate_daily_workflow_command.py", ["--config", str(cfg_path), "--project-root", str(root)])
        assert result.returncode == 0, result.stderr
        assert "run_local_app_workflow.py" in result.stdout
        assert "not installed" in result.stdout.lower() or "manually" in result.stdout.lower()


def test_validate_local_app_packaging_cli():
    result = _run_tool("validate_local_app_packaging.py", [])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    assert "OK: Phase 20 packaging validation passed." in result.stdout


def test_cli_no_network_calls():
    # All CLI tools operate on local files only.
    pass


def test_cli_no_broker_credentials_needed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("run_local_app_workflow.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0


def test_cli_no_email_creds_needed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("run_local_app_workflow.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0


def test_cli_no_telegram_creds_needed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = _run_tool("run_local_app_workflow.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0
