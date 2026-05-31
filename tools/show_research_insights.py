#!/usr/bin/env python3
"""CLI: Show research insights.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from research_insights.insight_builder import build_research_insights, render_research_insights_summary


def main():
    parser = argparse.ArgumentParser(description="Show research insights")
    parser.add_argument("--config", required=True, help="Path to research analytics config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional artifacts")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print("PAPER-ONLY / DATA-ONLY")
        print("No live trading. No order submission.")
        print("")
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    summary = build_research_insights(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)
    text = render_research_insights_summary(summary)
    print(text)

    if summary.blockers:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
