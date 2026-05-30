"""Tests for local app workflow and operations.

Covers:
- Environment check detects project root
- Environment check reports missing optional modules as warning
- Directory manager creates output dirs
- Workflow launcher skips disabled steps
- Workflow launcher records step status
- Workflow launcher writes summary JSON/Markdown
- Health bundle writes JSON
- Status summary includes next suggested command
- Backup local configs writes manifest
- Restore requires --confirm-restore
- Restore refuses path traversal
- Cleanup dry-run does not delete files
- Cleanup requires --confirm-cleanup
- Cleanup refuses source/test/example/data paths
- Scheduler command quotes project root with spaces
- Scheduler command uses venv python if available
- Dashboard launcher rejects nonlocal host by default
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from local_app.environment_check import check_environment
from local_app.directory_manager import create_directories
from local_app.workflow_launcher import run_workflow
from local_app.health_bundle import collect_health
from local_app.status_summary import build_status
from local_app.config_backup import backup_configs, restore_configs
from local_app.output_cleanup import preview_cleanup, perform_cleanup
from local_app.scheduler_chain import generate_daily_command
from local_app.app_config import load_config


def _make_config():
    return {
        "name": "test_local_app",
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


def test_environment_check_detects_project_root():
    result = check_environment(PROJECT_ROOT)
    assert result["healthy"] is True or result["healthy"] is False
    assert any("Project root exists" in o for o in result["ok"])


def test_environment_check_missing_modules_warning():
    # Create a fake empty project root
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result = check_environment(root)
        assert any("Missing optional" in w for w in result["warnings"])


def test_directory_manager_creates_output_dirs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        result = create_directories(cfg, root)
        assert result["success"]
        assert (root / "logs").exists()
        assert (root / "reports").exists()


def test_workflow_skips_disabled_steps():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        cfg["workflow"]["run_data_import"] = False
        summary = run_workflow(cfg, root)
        data_step = [s for s in summary["steps"] if s["step"] == "data_import"][0]
        assert data_step["status"] == "skipped"


def test_workflow_records_step_status():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        summary = run_workflow(cfg, root)
        for step in summary["steps"]:
            assert "status" in step
            assert step["status"] in ("skipped", "success", "warning", "failed")


def test_workflow_writes_summary_json_and_md():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        run_workflow(cfg, root)
        assert (root / "reports" / "local_app" / "workflow_summary.json").exists()
        assert (root / "reports" / "local_app" / "workflow_summary.md").exists()


def test_health_bundle_writes_json():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        health = collect_health(cfg, root, allow_missing=True)
        assert (root / "reports" / "local_app" / "health_check.json").exists()
        assert "overall" in health


def test_status_summary_includes_next_suggested_command():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        status = build_status(cfg, root)
        assert "run_local_app_workflow.py" in status["next_suggested_command"]


def test_backup_writes_manifest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        # Create a dummy config file to backup
        examples_dir = root / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / "briefing_config.example.json").write_text("{}")
        result = backup_configs(cfg, root)
        assert result["success"]
        backup_dir = root / result["backup_dir"]
        assert (backup_dir / "manifest.json").exists()


def test_restore_requires_confirm():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        backup_dir = root / "backups" / "local_configs" / "20260101T000000"
        backup_dir.mkdir(parents=True, exist_ok=True)
        result = restore_configs(backup_dir, root, confirm=False)
        assert not result["success"]
        assert "confirm-restore" in result["error"]


def test_restore_refuses_path_traversal():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        backup_dir = Path(td) / "backups" / "local_configs" / "20260101T000000"
        backup_dir.mkdir(parents=True, exist_ok=True)
        # Create manifest with a path outside project root
        manifest = {
            "timestamp": "20260101T000000",
            "copied": ["../outside_config.json"],
        }
        (backup_dir / "manifest.json").write_text(json.dumps(manifest))
        result = restore_configs(backup_dir, root, confirm=True)
        assert not result["success"] or any("Path traversal" in e for e in result.get("errors", []))


def test_cleanup_dry_run_does_not_delete():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        # Create a file in a safe cleanup dir
        safe_dir = root / "reports" / "briefing"
        safe_dir.mkdir(parents=True, exist_ok=True)
        test_file = safe_dir / "test.txt"
        test_file.write_text("hello")
        preview = preview_cleanup(cfg, root)
        assert test_file.exists()
        assert any("reports/briefing/test.txt" in f for f in preview["would_delete"])


def test_cleanup_requires_confirm():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        result = perform_cleanup(cfg, root, confirm=False)
        assert not result["success"]
        assert "confirm-cleanup" in result["error"]


def test_cleanup_refuses_source_paths():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        # Try to trick cleanup into deleting strategies/
        # The _is_safe_to_delete function should refuse
        safe_dir = root / "reports" / "briefing"
        safe_dir.mkdir(parents=True, exist_ok=True)
        # This is still in reports/briefing so it should be allowed
        # But we verify the safety function works for forbidden paths
        from local_app.output_cleanup import _is_safe_to_delete
        forbidden = root / "strategies" / "test.py"
        forbidden.parent.mkdir(parents=True, exist_ok=True)
        forbidden.write_text("code")
        assert not _is_safe_to_delete(forbidden, root)


def test_scheduler_quotes_project_root_with_spaces():
    with tempfile.TemporaryDirectory() as td:
        # Create a path with spaces (using a subdir)
        root = Path(td) / "My Quant Agent"
        root.mkdir()
        cfg = _make_config()
        result = generate_daily_command(cfg, root)
        assert "My Quant Agent" in result["command"]
        assert '"' in result["command"] or "\\ " in result["command"]


def test_scheduler_uses_venv_python_if_available():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        venv_python = root / "venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True, exist_ok=True)
        venv_python.write_text("#!/bin/bash\n")
        cfg = _make_config()
        result = generate_daily_command(cfg, root)
        assert "venv/bin/python" in result["command"]


def test_dashboard_rejects_nonlocal_host_by_default():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = _make_config()
        cfg["dashboard"]["host"] = "0.0.0.0"
        from local_app.app_config import validate_config
        result = validate_config(cfg)
        assert not result["valid"]
        assert any("0.0.0.0 rejected" in e for e in result["errors"])
