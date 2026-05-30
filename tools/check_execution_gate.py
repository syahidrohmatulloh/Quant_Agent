#!/usr/bin/env python3
"""CLI: check execution gate.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
No broker calls. No live network.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from readiness_gate.readiness_config import load_readiness_config
from readiness_gate.execution_gate_audit import run_execution_gate_audit


def main():
    parser = argparse.ArgumentParser(description="Check execution gate")
    parser.add_argument("--config", required=True, help="Path to readiness config JSON")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")
    print("No broker calls. No live network.")

    config = load_readiness_config(Path(args.config))
    project_root = Path(config.project_root).resolve()
    audit = run_execution_gate_audit(project_root, config.include_dirs, config.exclude_dirs)

    print(f"Execution gate audit: {audit.pass_count} pass, {audit.fail_count} fail")
    if audit.fail_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
