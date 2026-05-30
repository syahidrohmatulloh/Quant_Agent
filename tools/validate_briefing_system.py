#!/usr/bin/env python3
"""CLI: Validate Phase 19 briefing system.

Imports all new modules, py_compiles new files, scans for safety.
"""

from pathlib import Path
import sys
import py_compile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def scan_file_for_forbidden(path: Path) -> list:
    """Scan a file for contiguous forbidden strings."""
    forbidden = [
        "order" + "_send",
        "execute" + "_order",
        "place" + "_order",
        "submit" + "_order",
        "telegram" + "_token",
        "bot" + "_token",
        "smtp" + "_password",
    ]
    issues = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return []
    for fb in forbidden:
        if fb in raw:
            issues.append(f"Found forbidden string: {fb}")
    return issues


def main():
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print()

    # Import all new modules
    modules = [
        "briefing",
        "briefing.briefing_config",
        "briefing.source_loader",
        "briefing.alert_rules",
        "briefing.signal_alerts",
        "briefing.risk_alerts",
        "briefing.data_quality_alerts",
        "briefing.pnl_alerts",
        "briefing.briefing_builder",
        "briefing.briefing_report",
        "briefing.message_templates",
        "briefing.dashboard_export",
        "briefing.briefing_log",
        "briefing.scheduler_plan",
    ]

    ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"OK  import {mod}")
        except Exception as e:
            print(f"FAIL import {mod}: {e}")
            ok = False

    # py_compile new files
    new_files = [
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

    for rel in new_files:
        p = PROJECT_ROOT / rel
        if not p.exists():
            print(f"FAIL missing file: {rel}")
            ok = False
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            print(f"OK  py_compile {rel}")
        except py_compile.PyCompileError as e:
            print(f"FAIL py_compile {rel}: {e}")
            ok = False

    # Safety scan Phase 19 only
    print()
    print("Safety scan (Phase 19 files only)...")
    safety_ok = True
    for rel in new_files:
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        issues = scan_file_for_forbidden(p)
        if issues:
            for issue in issues:
                print(f"WARN {rel}: {issue}")
            safety_ok = False
        else:
            print(f"OK  safety {rel}")

    print()
    if ok and safety_ok:
        print("OK: Phase 19 briefing system validation passed.")
        sys.exit(0)
    else:
        print("FAIL: Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
