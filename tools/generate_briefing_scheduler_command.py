#!/usr/bin/env python3
"""CLI: Generate scheduler command suggestion.

Does NOT install cron. Only prints a command.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from briefing.briefing_config import load_config, validate_config
from briefing.scheduler_plan import generate_scheduler_plan


def main():
    parser = argparse.ArgumentParser(description="Generate scheduler command suggestion")
    parser.add_argument("--config", required=True, help="Path to briefing config JSON")
    parser.add_argument("--project-root", default=".", help="Project root path")
    parser.add_argument("--venv-python", default="python3", help="Python executable path")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("NOTE: This tool only prints a command. It does NOT install any scheduler.")
    print()

    config_path = Path(args.config)
    config = load_config(config_path)
    validation = validate_config(config, allow_missing=True)
    if not validation["valid"]:
        print("Config validation failed:")
        for err in validation["errors"]:
            print(f"  - {err}")
        sys.exit(1)

    project_root = Path(args.project_root).resolve()
    plan = generate_scheduler_plan(config, project_root, venv_python=args.venv_python)
    print(plan)
    print()
    print("Copy the cron line above into your crontab manually if desired.")
    print("Review before enabling. Paper-only / data-only.")


if __name__ == "__main__":
    main()
