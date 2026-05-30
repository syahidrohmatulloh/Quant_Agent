#!/usr/bin/env python3
"""CLI: check paper-only safety.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from readiness_gate.readiness_config import load_readiness_config
from readiness_gate.safety_audit import run_safety_audit


def main():
    parser = argparse.ArgumentParser(description="Check paper-only safety")
    parser.add_argument("--config", required=True, help="Path to readiness config JSON")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")

    config = load_readiness_config(Path(args.config))
    project_root = Path(config.project_root).resolve()
    audit = run_safety_audit(project_root, config.audit_rules)

    print(f"Safety audit: {audit.pass_count} pass, {audit.warning_count} warning, {audit.fail_count} fail")
    if audit.fail_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
