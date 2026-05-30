#!/usr/bin/env python3
"""CLI: Run local app workflow.

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.workflow_launcher import run_workflow
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Run local app workflow")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing config files")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="Project root path")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print_disclaimer()
    print()

    config_path = project_root / Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"FAIL: Could not load config: {e}")
        sys.exit(1)

    summary = run_workflow(config, project_root, allow_missing=args.allow_missing)

    print(f"Workflow status: {summary['overall_status']}")
    for step in summary["steps"]:
        print(f"  {step['step']}: {step['status']} - {step['message']}")
    print(f"Summary written to: reports/local_app/workflow_summary.json")
    print(f"Summary written to: reports/local_app/workflow_summary.md")
    print("OK: Workflow complete.")
    sys.exit(0 if summary["overall_status"] == "success" else 1)


if __name__ == "__main__":
    main()
