#!/usr/bin/env python3
"""CLI: Validate the entire paper orchestration module.
Runs py_compile on all Phase 15 new files.
Paper-only.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import py_compile
import argparse


def main():
    parser = argparse.ArgumentParser(description="Validate paper orchestration module.")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    files_to_check = [
        "paper_orchestration/__init__.py",
        "paper_orchestration/orchestration_config.py",
        "paper_orchestration/daily_runner.py",
        "paper_orchestration/paper_portfolio.py",
        "paper_orchestration/paper_decision.py",
        "paper_orchestration/risk_guard.py",
        "paper_orchestration/audit_log.py",
        "paper_orchestration/dashboard_refresh.py",
        "paper_orchestration/scheduler_plan.py",
        "tools/validate_orchestration_config.py",
        "tools/run_daily_paper_workflow.py",
        "tools/show_paper_portfolio.py",
        "tools/reset_paper_portfolio.py",
        "tools/generate_scheduler_command.py",
        "tools/validate_paper_orchestration.py",
    ]

    all_ok = True
    for rel in files_to_check:
        p = PROJECT_ROOT / rel
        try:
            py_compile.compile(str(p), doraise=True)
            print("OK   " + rel)
        except py_compile.PyCompileError as e:
            print("FAIL " + rel + " : " + str(e))
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
