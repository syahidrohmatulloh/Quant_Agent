#!/usr/bin/env python3
"""CLI: Validate local app packaging.

Imports all new modules, py_compiles new files, scans Phase 20 for safety.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import py_compile

from local_app.safety import print_disclaimer

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
]

# Forbidden contiguous strings (built via concatenation to avoid them in this file too)
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


def main():
    print_disclaimer()
    print()

    all_ok = True
    issues = []

    # 1. Import all new modules
    try:
        import local_app.app_config
        import local_app.environment_check
        import local_app.directory_manager
        import local_app.workflow_launcher
        import local_app.health_bundle
        import local_app.config_backup
        import local_app.output_cleanup
        import local_app.status_summary
        import local_app.scheduler_chain
        import local_app.safety
        print("OK: All new modules imported successfully.")
    except Exception as e:
        print(f"FAIL: Module import error: {e}")
        all_ok = False

    # 2. py_compile all new files
    for rel in _PHASE20_FILES:
        p = PROJECT_ROOT / rel
        if not p.exists():
            issues.append(f"Missing file: {rel}")
            all_ok = False
            continue
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            issues.append(f"py_compile failed for {rel}: {e}")
            all_ok = False

    if not any("py_compile failed" in i for i in issues):
        print("OK: py_compile passed for all new files.")

    # 3. Scan Phase 20 files for forbidden strings
    forbidden_issues = []
    for rel in _PHASE20_FILES:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        text = p.read_text()
        for fb in _FORBIDDEN:
            if fb in text:
                forbidden_issues.append(f"{rel}: contains forbidden string {fb}")
                all_ok = False

    if forbidden_issues:
        print("FAIL: Forbidden strings found:")
        for fi in forbidden_issues:
            print(f"  {fi}")
    else:
        print("OK: No forbidden contiguous strings found in Phase 20 files.")

    # 4. Check for generated outputs in patch-sensitive locations
    sensitive_dirs = ["reports", "logs", "data/market", "data/raw_imports", "local_configs"]
    found_sensitive = []
    for d in sensitive_dirs:
        p = PROJECT_ROOT / d
        if p.exists() and any(p.iterdir()):
            found_sensitive.append(d)

    if found_sensitive:
        print(f"WARNING: Generated outputs detected in: {found_sensitive}")
    else:
        print("OK: No generated outputs in patch-sensitive locations.")

    if issues:
        print("Other issues:")
        for i in issues:
            print(f"  {i}")

    if all_ok:
        print("OK: Phase 20 packaging validation passed.")
        sys.exit(0)
    else:
        print("FAIL: Phase 20 packaging validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
