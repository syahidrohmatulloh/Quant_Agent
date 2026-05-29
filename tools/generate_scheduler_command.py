#!/usr/bin/env python3
"""CLI: Generate cron-friendly scheduler command.
Does not install cron. Only prints the command.
Paper-only.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from paper_orchestration.scheduler_plan import generate_scheduler_command


def main():
    parser = argparse.ArgumentParser(description="Generate scheduler command for daily paper workflow.")
    parser.add_argument("--config", required=True, help="Path to orchestration config JSON")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    cmd = generate_scheduler_command(args.config, project_root=args.project_root)
    print("\nSuggested cron command (review before enabling):")
    print(cmd)
    print("\nDisclaimer: This command is for manual review only.")
    print("It is NOT installed automatically. Add it to your crontab manually if desired.")
    print("Default schedule suggestion: once per day or manually triggered.")


if __name__ == "__main__":
    main()
