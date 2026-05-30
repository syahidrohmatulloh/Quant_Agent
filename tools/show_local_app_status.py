#!/usr/bin/env python3
"""CLI: Show local app status.

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.status_summary import build_status
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Show local app status")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing config files")
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

    status = build_status(config, PROJECT_ROOT)

    print("Phase Readiness:")
    for phase, ready in status["phases_ready"].items():
        print(f"  {phase}: {'ready' if ready else 'not ready'}")
    print("Latest Reports:")
    for subdir, latest in status["latest_reports"].items():
        print(f"  {subdir}: {latest or 'none'}")
    print("Directories:")
    for name, info in status["directories"].items():
        print(f"  {name}: {info['path']} ({'exists' if info['exists'] else 'missing'})")
    if status["warnings"]:
        print("Warnings:")
        for w in status["warnings"]:
            print(f"  {w}")
    print(f"Next suggested command: {status['next_suggested_command']}")
    print("OK: Status displayed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
