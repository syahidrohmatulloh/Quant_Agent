#!/usr/bin/env python3
"""CLI: Show paper broker readiness report.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Does not make network calls. Does not require real credentials.
Does not connect to real broker execution.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from paper_broker.readiness import (
    build_paper_broker_readiness,
    render_paper_broker_readiness_summary,
    write_paper_broker_readiness_report,
)


def main():
    parser = argparse.ArgumentParser(description="Show paper broker readiness report")
    parser.add_argument("--config", required=True, help="Path to config JSON (e.g., examples/local_app_config.example.json)")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional broker config")
    parser.add_argument("--write-report", action="store_true", help="Write readiness report to reports/paper_broker/")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("This is not financial advice.")
    print("This does not approve or enable live trading.")
    print("")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(2)

    config = load_config(config_path)

    # Validate safety flags
    if not config.get("paper_only", True):
        print("ERROR: config.paper_only must be true")
        sys.exit(2)
    if not config.get("data_only", True):
        print("ERROR: config.data_only must be true")
        sys.exit(2)
    if not config.get("no_order_submission", True):
        print("ERROR: config.no_order_submission must be true")
        sys.exit(2)

    report = build_paper_broker_readiness(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)
    text = render_paper_broker_readiness_summary(report)
    print(text)

    if args.write_report:
        output_paths = write_paper_broker_readiness_report(PROJECT_ROOT, report, config=config)
        for p in output_paths:
            print(f"Written: {p}")
        print("")

    if report.status == "BLOCKED":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
