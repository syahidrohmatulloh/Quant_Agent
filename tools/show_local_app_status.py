#!/usr/bin/env python3
"""CLI: Show local app status.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from local_app.status_summary import build_status


def main():
    parser = argparse.ArgumentParser(description="Show local app status")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    status = build_status(config, PROJECT_ROOT)

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("")

    print("=" * 50)
    print("Safety Mode")
    print("=" * 50)
    print(f"  Mode:        {status.get('safety_mode', 'PAPER-ONLY / DATA-ONLY')}")
    print(f"  Paper-only:  {status.get('paper_only', True)}")
    print(f"  Data-only:   {status.get('data_only', True)}")
    print(f"  No " + "order" + " submission: {status.get('no_order_submission', True)}")
    print("")

    print("=" * 50)
    print("Phase Readiness")
    print("=" * 50)
    for phase, ready in status["phases_ready"].items():
        marker = "READY" if ready else "MISSING"
        print(f"  {phase}: {marker}")
    print("")

    print("=" * 50)
    print("Latest Reports")
    print("=" * 50)
    for report_type, path in status["latest_reports"].items():
        if path:
            print(f"  {report_type}: {path}")
        else:
            print(f"  {report_type}: None")
    print("")

    print("=" * 50)
    print("Local Outputs")
    print("=" * 50)
    for out_name, out_info in status.get("local_outputs", {}).items():
        exists = "EXISTS" if out_info.get("exists") else "MISSING"
        count = out_info.get("file_count", 0)
        print(f"  {out_name}: {exists} ({count} files)")
    print("")

    print("=" * 50)
    print("Readiness")
    print("=" * 50)
    readiness = status.get("readiness", {})
    if readiness.get("available"):
        print(f"  Score:  {readiness.get('score', 'N/A')}/100")
        print(f"  Grade:  {readiness.get('grade', 'N/A')}")
        print(f"  Status: {readiness.get('status', 'N/A')}")
        print(f"  Path:   {readiness.get('path', 'N/A')}")
    else:
        print("  No readiness report available.")
    print("")

    print("=" * 50)
    print("Briefing")
    print("=" * 50)
    briefing = status.get("briefing", {})
    if briefing.get("available"):
        print(f"  Latest: {briefing.get('latest', 'N/A')}")
    else:
        print("  No briefing output available.")
    print("")

    print("=" * 50)
    print("Dashboard")
    print("=" * 50)
    dashboard = status.get("dashboard", {})
    if dashboard.get("available"):
        print(f"  Latest: {dashboard.get('latest', 'N/A')}")
    else:
        print("  No dashboard export available.")
    print("")

    print("=" * 50)
    print("Directories")
    print("=" * 50)
    for name, info in status["directories"].items():
        marker = "EXISTS" if info["exists"] else "MISSING"
        print(f"  {name}: {info['path']} ({marker})")
    print("")

    print("=" * 50)
    print("Warnings")
    print("=" * 50)
    if status["warnings"]:
        for w in status["warnings"]:
            print(f"  - {w}")
    else:
        print("  None")
    print("")

    print("=" * 50)
    print("Next Safe Commands")
    print("=" * 50)
    for cmd in status.get("next_safe_commands", []):
        print(f"  $ {cmd}")
    print("")

    print("=" * 50)
    print("Next Command")
    print("=" * 50)
    print("Next suggested command:")
    print(f"  {status['next_suggested_command']}")
    print("")


if __name__ == "__main__":
    main()
