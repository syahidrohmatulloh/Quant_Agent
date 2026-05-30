#!/usr/bin/env python3
"""CLI: Initialize local app directories.

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.directory_manager import create_directories
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Initialize local app directories")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
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

    result = create_directories(config, project_root)

    if result["created"]:
        print("Created directories:")
        for d in result["created"]:
            print(f"  {d}")
    if result["warnings"]:
        print("Warnings:")
        for w in result["warnings"]:
            print(f"  {w}")
    if result["errors"]:
        print("Errors:")
        for e in result["errors"]:
            print(f"  {e}")
        sys.exit(1)

    print("OK: Directories initialized.")
    sys.exit(0)


if __name__ == "__main__":
    main()
