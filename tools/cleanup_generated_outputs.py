#!/usr/bin/env python3
"""CLI: Cleanup generated outputs.

Dry-run by default. Requires --confirm-cleanup for actual deletion.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from local_app.app_config import load_config
from local_app.output_cleanup import preview_cleanup, perform_cleanup
from local_app.safety import print_disclaimer


def main():
    parser = argparse.ArgumentParser(description="Cleanup generated outputs")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--confirm-cleanup", action="store_true", help="Confirm actual deletion")
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

    if args.dry_run or not args.confirm_cleanup:
        preview = preview_cleanup(config, PROJECT_ROOT)
        print(f"Dry-run: would delete {preview['count']} files")
        for f in preview["would_delete"]:
            print(f"  {f}")
        print("Use --confirm-cleanup to proceed with deletion.")
        sys.exit(0)

    result = perform_cleanup(config, PROJECT_ROOT, confirm=args.confirm_cleanup)

    if not result["success"]:
        print(f"FAIL: {result.get('error', 'Unknown error')}")
        if result.get("errors"):
            for err in result["errors"]:
                print(f"  {err}")
        sys.exit(1)

    print(f"Deleted {result['count']} files:")
    for f in result.get("deleted", []):
        print(f"  {f}")
    if result.get("errors"):
        print("Errors:")
        for err in result["errors"]:
            print(f"  {err}")
    print("OK: Cleanup complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()
