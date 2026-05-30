#!/usr/bin/env python3
"""CLI: validate readiness gate itself.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
"""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_forbidden():
    """Build forbidden string list using safe concatenation."""
    exec_parts = [
        ("order", "_send"),
        ("execute", "_order"),
        ("place", "_order"),
        ("submit", "_order"),
    ]
    cred_parts = [
        ("telegram", "_token"),
        ("bot", "_token"),
        ("smtp", "_password"),
    ]
    path_parts = [
        ("/mnt/agents", "/output"),
        ("/Users/", "syahidrohmatulloh"),
    ]
    forbidden = []
    for a, b in exec_parts + cred_parts:
        forbidden.append(a + b)
    for a, b in path_parts:
        forbidden.append(a + b)
    return forbidden


def main():
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")

    modules = [
        "readiness_gate/__init__.py",
        "readiness_gate/readiness_config.py",
        "readiness_gate/source_inventory.py",
        "readiness_gate/safety_audit.py",
        "readiness_gate/credential_audit.py",
        "readiness_gate/execution_gate_audit.py",
        "readiness_gate/risk_control_audit.py",
        "readiness_gate/config_audit.py",
        "readiness_gate/output_hygiene_audit.py",
        "readiness_gate/test_status_audit.py",
        "readiness_gate/readiness_score.py",
        "readiness_gate/readiness_report.py",
        "readiness_gate/dashboard_export.py",
        "readiness_gate/readiness_log.py",
        "tools/validate_readiness_config.py",
        "tools/run_readiness_audit.py",
        "tools/check_paper_only_safety.py",
        "tools/check_credential_exposure.py",
        "tools/check_execution_gate.py",
        "tools/generate_readiness_report.py",
        "tools/export_readiness_dashboard.py",
        "tools/validate_readiness_gate.py",
    ]

    tests = [
        "tests/readiness_gate/test_phase21_readiness_config.py",
        "tests/readiness_gate/test_phase21_readiness_audit.py",
        "tests/readiness_gate/test_phase21_readiness_report.py",
        "tests/tools/test_phase21_readiness_gate_cli_tools.py",
    ]

    all_ok = True
    for rel in modules + tests:
        path = PROJECT_ROOT / rel
        if not path.exists():
            print("MISSING: " + rel)
            all_ok = False
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            print("OK: " + rel)
        except py_compile.PyCompileError as e:
            print("FAIL: " + rel + " - " + str(e))
            all_ok = False

    # Scan Phase 21 new files only for forbidden contiguous strings
    # Skip readiness_gate and test files because they legitimately contain these strings for validation/testing
    forbidden = _build_forbidden()

    # Only scan non-audit tools and non-test files
    scan_targets = [
        "tools/validate_readiness_config.py",
        "tools/run_readiness_audit.py",
        "tools/check_paper_only_safety.py",
        "tools/check_credential_exposure.py",
        "tools/check_execution_gate.py",
        "tools/generate_readiness_report.py",
        "tools/export_readiness_dashboard.py",
    ]

    for rel in scan_targets:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for word in forbidden:
            if word in content:
                print("FORBIDDEN: " + rel + " contains '" + word + "'")
                all_ok = False

    if all_ok:
        print("All Phase 21 files compile and pass safety scan.")
        sys.exit(0)
    else:
        print("Some Phase 21 files failed validation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
