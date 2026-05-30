#!/usr/bin/env python3
"""CLI: Generate daily workflow command for scheduler.

Prints command for review. Does not install cron.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.scheduler_chain import generate_daily_command
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Generate daily workflow command")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--project-root", default=".", help="Project root path")
    args = parser.parse_args()

    print_disclaimer()
    print()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config file not found: {config_path}")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"FAIL: Could not load config: {e}")
        sys.exit(1)

    project_root = Path(args.project_root).resolve()
    result = generate_daily_command(config, project_root, args.config)

    print("Suggested daily workflow command:")
    print(result["command"])
    print(f"Suggested time: {result['suggested_time']}")
    print(f"Timezone: {result['timezone']}")
    print(f"Log path: {result['log_path']}")
    print(f"Disclaimer: {result['disclaimer']}")
    print("OK: Command generated.")
    sys.exit(0)


if __name__ == "__main__":
    main()
