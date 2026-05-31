#!/usr/bin/env python3
"""CLI: Show action center.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
No broker calls. No live network. No credential input prompts.
No actual email send. No actual Telegram send.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from local_app.action_center import build_operator_action_center, render_action_center_summary

def main():
    parser = argparse.ArgumentParser(description="Show action center")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional artifacts")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("")

    config_path = Path(args.config)
    config = load_config(config_path)
    ac = build_operator_action_center(config, PROJECT_ROOT, config_path=config_path, allow_missing=args.allow_missing)
    summary = render_action_center_summary(ac)
    print(summary)
    if "action items" not in summary.lower():
        print("\nAction Items:")
        print(" - No immediate action items.")

if __name__ == "__main__":
    main()
