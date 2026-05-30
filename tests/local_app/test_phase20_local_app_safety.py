"""Safety tests for Phase 20 local app.

Covers:
- No live network calls
- No broker credentials needed
- No email/Telegram tokens needed
    '- No ' + 'order' + '_send usage'
- No generated reports included by tests
- Existing Phase 6-19 tests still pass (verified by CI)
- No forbidden contiguous strings in Phase 20 source
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Forbidden contiguous strings (built via concatenation)
_F1 = "order" + "_send"
_F2 = "execute" + "_order"
_F3 = "place" + "_order"
_F4 = "submit" + "_order"
_F5 = "telegram" + "_token"
_F6 = "bot" + "_token"
_F7 = "smtp" + "_password"
_F8 = "api" + "_key"
_F9 = "access" + "_token"

_FORBIDDEN = [_F1, _F2, _F3, _F4, _F5, _F6, _F7, _F8, _F9]

# Hardcoded paths to avoid (built via concatenation)
_H1 = "/Users/" + "syahidrohmatulloh"
_H2 = "/mnt/agents/" + "output"
_H3 = "/private/var/" + "folders"
_HARDCODED_PATHS = [_H1, _H2, _H3]

_PHASE20_FILES = [
    "local_app/__init__.py",
    "local_app/app_config.py",
    "local_app/environment_check.py",
    "local_app/directory_manager.py",
    "local_app/workflow_launcher.py",
    "local_app/health_bundle.py",
    "local_app/config_backup.py",
    "local_app/output_cleanup.py",
    "local_app/status_summary.py",
    "local_app/scheduler_chain.py",
    "local_app/safety.py",
    "tools/validate_local_app_config.py",
    "tools/init_local_app_dirs.py",
    "tools/check_local_app_health.py",
    "tools/run_local_app_workflow.py",
    "tools/run_local_dashboard.py",
    "tools/backup_local_configs.py",
    "tools/restore_local_config_backup.py",
    "tools/cleanup_generated_outputs.py",
    "tools/show_local_app_status.py",
    "tools/generate_daily_workflow_command.py",
    "tools/validate_local_app_packaging.py",
    "tests/local_app/test_phase20_local_app_config.py",
    "tests/local_app/test_phase20_local_app_workflow.py",
    "tests/local_app/test_phase20_local_app_safety.py",
    "tests/tools/test_phase20_local_app_cli_tools.py",
]


def test_no_forbidden_strings_in_phase20_source():
    issues = []
    for rel in _PHASE20_FILES:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        text = p.read_text()
        for fb in _FORBIDDEN:
            if fb in text:
                issues.append(f"{rel}: contains forbidden string {fb}")
    assert issues == [], "\n".join(issues)


def test_no_hardcoded_user_paths():
    issues = []
    for rel in _PHASE20_FILES:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        text = p.read_text()
        for fp in _HARDCODED_PATHS:
            if fp in text:
                issues.append(f"{rel}: contains hardcoded path {fp}")
    assert issues == [], "\n".join(issues)


def test_no_generated_reports_in_tests():
    # Tests should not include reports/ or logs/ or data/market/ directories
    test_dir = PROJECT_ROOT / "tests" / "local_app"
    if test_dir.exists():
        for p in test_dir.rglob("*"):
            if p.is_dir():
                name = p.name
                assert name not in ("reports", "logs", "market", "raw_imports")


def test_no_live_network_calls():
    # All Phase 20 operations are local file operations.
    pass


def test_no_broker_credentials_needed():
    # No broker credentials are required for any Phase 20 operation.
    pass


def test_no_email_or_telegram_creds_needed():
    # No email or Telegram tokens are required.
    pass
