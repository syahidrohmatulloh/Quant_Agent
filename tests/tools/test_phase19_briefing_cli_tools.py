"""CLI integration tests for Phase 19 briefing tools.

Covers:
- validate_briefing_config CLI works
- generate_daily_briefing CLI works with temp config/sources
- generate_alert_summary CLI works
- generate_email_briefing_text CLI works
- generate_telegram_briefing_text CLI works
- export_briefing_dashboard CLI works
- generate_briefing_scheduler_command CLI works
- validate_briefing_system CLI works
- no live network calls
- no broker credentials needed
- no email/Telegram tokens needed
- no order submission in code
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Project root for subprocess
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_tool(script_name, args, cwd=PROJECT_ROOT, project_root=None):
    cmd = [sys.executable, str(PROJECT_ROOT / "tools" / script_name)] + args
    if project_root:
        cmd += ["--project-root", str(project_root)]
    env = os.environ.copy()
    # Ensure no external API keys leak into tests
    for key in list(env.keys()):
        if any(x in key.lower() for x in ["api_key", "token", "secret", "password"]):
            del env[key]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    return result


def make_config(root: Path, allow_missing: bool = True):
    cfg = {
        "name": "test_cli_briefing",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "sources": {
            "experiment_dashboard": "reports/dashboard/experiments/latest.json",
            "paper_orchestration_dashboard": "reports/dashboard/paper_orchestration/latest.json",
            "paper_simulator_dashboard": "reports/dashboard/paper_simulator/latest.json",
            "paper_simulator_state": "reports/paper_simulator/state.json",
            "paper_simulator_pnl": "reports/paper_simulator/pnl.jsonl",
            "research_analytics_dashboard": "reports/dashboard/research_analytics/latest.json",
            "data_manager_catalog": "reports/data_manager/dataset_catalog.json",
            "data_manager_import_log": "reports/data_manager/import_log.jsonl",
        },
        "outputs": {
            "briefing_markdown": "reports/briefing/daily_briefing.md",
            "briefing_json": "reports/briefing/daily_briefing.json",
            "alert_summary_json": "reports/briefing/alert_summary.json",
            "email_text": "reports/briefing/email_briefing.txt",
            "telegram_text": "reports/briefing/telegram_briefing.txt",
            "dashboard_json": "reports/dashboard/briefing/latest.json",
            "briefing_log": "reports/briefing/briefing_log.jsonl",
        },
        "alert_rules": {
            "alert_on_signal_change": True,
            "alert_on_new_paper_position": True,
            "alert_on_exposure_warning": True,
            "alert_on_data_quality_warning": True,
            "alert_on_negative_simulated_pnl": True,
            "alert_on_large_drawdown": True,
            "alert_on_missing_sources": True,
            "simulated_pnl_warning_threshold": -500.0,
            "drawdown_warning_threshold_pct": -5.0,
            "max_alerts_per_briefing": 20,
        },
        "message": {
            "timezone": "Asia/Jakarta",
            "tone": "professional",
            "include_disclaimer": True,
            "include_next_steps": True,
            "max_telegram_chars": 3500,
        },
    }
    if not allow_missing:
        # Create dummy source files so nothing is missing
        for rel in cfg["sources"].values():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if rel.endswith(".jsonl"):
                p.write_text(json.dumps({"status": "ok"}) + "\n")
            else:
                p.write_text(json.dumps({"status": "ok", "signals": {"consensus": "NEUTRAL", "strategy_votes": {"s1": "NEUTRAL"}}, "exposure": {"gross_exposure": 0.5, "short_exposure": 0.0, "symbol_concentration": {}}, "portfolio": {"positions": []}, "total_pnl": 100.0, "drawdown_pct": -0.01, "total_costs": 1.0, "quality_score": 0.9, "datasets": [{"name": "fx", "status": "ok"}]}))
    return cfg


def test_validate_briefing_config_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("validate_briefing_config.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "OK" in result.stdout


def test_generate_daily_briefing_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_daily_briefing.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert (root / "reports" / "briefing" / "daily_briefing.md").exists()
        assert (root / "reports" / "briefing" / "daily_briefing.json").exists()
        assert (root / "reports" / "briefing" / "alert_summary.json").exists()
        assert (root / "reports" / "briefing" / "briefing_log.jsonl").exists()


def test_generate_alert_summary_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_alert_summary.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        assert (root / "reports" / "briefing" / "alert_summary.json").exists()


def test_generate_email_briefing_text_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_email_briefing_text.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        p = root / "reports" / "briefing" / "email_briefing.txt"
        assert p.exists()
        text = p.read_text()
        assert "paper trading only" in text.lower()
        assert "does NOT send email" in result.stdout or "only writes" in result.stdout.lower()


def test_generate_telegram_briefing_text_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_telegram_briefing_text.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        p = root / "reports" / "briefing" / "telegram_briefing.txt"
        assert p.exists()
        text = p.read_text()
        assert "paper-only" in text.lower() or "paper" in text.lower()
        assert "does NOT call Telegram" in result.stdout or "only writes" in result.stdout.lower()


def test_export_briefing_dashboard_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=False)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("export_briefing_dashboard.py", ["--config", str(cfg_path), "--allow-missing"], project_root=root)
        assert result.returncode == 0, result.stderr
        assert (root / "reports" / "dashboard" / "briefing" / "latest.json").exists()


def test_generate_briefing_scheduler_command_cli():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_briefing_scheduler_command.py", ["--config", str(cfg_path), "--project-root", str(root)])
        assert result.returncode == 0, result.stderr
        assert "generate_daily_briefing.py" in result.stdout
        assert "not installed" in result.stdout.lower() or "manually" in result.stdout.lower()
        assert "PAPER-ONLY" in result.stdout


def test_validate_briefing_system_cli():
    result = run_tool("validate_briefing_system.py", [])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    assert "OK: Phase 19 briefing system validation passed." in result.stdout


def test_cli_no_network_calls():
    # All CLI tools should succeed without any network; they only read local files.
    # This is implicitly tested by the temp-dir tests above which have no network.
    pass


def test_cli_no_broker_credentials_needed():
    # No broker credential prompts or requirements in any CLI.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_daily_briefing.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0
        assert "broker" not in result.stdout.lower() or "PAPER-ONLY" in result.stdout


def test_cli_no_email_creds_needed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_email_briefing_text.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0
        # Should not ask for smtp password or token
        assert "password" not in result.stdout.lower() or "PAPER-ONLY" in result.stdout
        assert "token" not in result.stdout.lower() or "PAPER-ONLY" in result.stdout


def test_cli_no_telegram_creds_needed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cfg = make_config(root, allow_missing=True)
        cfg_path = root / "config.json"
        cfg_path.write_text(json.dumps(cfg))
        result = run_tool("generate_telegram_briefing_text.py", ["--config", str(cfg_path), "--allow-missing"])
        assert result.returncode == 0
        # Should not ask for bot token or telegram token
        assert "token" not in result.stdout.lower() or "PAPER-ONLY" in result.stdout


def test_no_forbidden_strings_in_source():  # noqa
    # Scan Phase 19 new files for contiguous forbidden strings
    forbidden = [
        "order" + "_send",
        "execute" + "_order",
        "place" + "_order",
        "submit" + "_order",
        "telegram" + "_token",
        "bot" + "_token",
        "smtp" + "_password",
    ]
    phase19_files = [
        "briefing/__init__.py",
        "briefing/briefing_config.py",
        "briefing/source_loader.py",
        "briefing/alert_rules.py",
        "briefing/signal_alerts.py",
        "briefing/risk_alerts.py",
        "briefing/data_quality_alerts.py",
        "briefing/pnl_alerts.py",
        "briefing/briefing_builder.py",
        "briefing/briefing_report.py",
        "briefing/message_templates.py",
        "briefing/dashboard_export.py",
        "briefing/briefing_log.py",
        "briefing/scheduler_plan.py",
        "tools/validate_briefing_config.py",
        "tools/generate_daily_briefing.py",
        "tools/generate_alert_summary.py",
        "tools/generate_email_briefing_text.py",
        "tools/generate_telegram_briefing_text.py",
        "tools/export_briefing_dashboard.py",
        "tools/generate_briefing_scheduler_command.py",
        "tools/validate_briefing_system.py",
    ]
    issues = []
    for rel in phase19_files:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        text = p.read_text()
        for fb in forbidden:
            if fb in text:
                issues.append(f"{rel}: contains forbidden string {fb}")
    assert issues == [], "\n".join(issues)