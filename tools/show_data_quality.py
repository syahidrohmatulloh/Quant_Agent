#!/usr/bin/env python3
"""CLI: Show data quality center report.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Scans market data CSV files and reports quality issues.
Does not modify files.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from data_quality.quality_report import (
    build_data_quality_report,
    render_data_quality_summary,
    write_data_quality_report,
)


def main():
    parser = argparse.ArgumentParser(description="Show data quality center report")
    parser.add_argument("--config", required=True, help="Path to market data import config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional data directories and files")
    parser.add_argument("--write-report", action="store_true", help="Write quality report to reports/data_quality/")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Validate safety flags
    if not config.get("paper_only", True):
        print("ERROR: config.paper_only must be true")
        sys.exit(1)
    if not config.get("data_only", True):
        print("ERROR: config.data_only must be true")
        sys.exit(1)
    if not config.get("no_order_submission", True):
        print("ERROR: config.no_order_submission must be true")
        sys.exit(1)

    report = build_data_quality_report(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)
    text = render_data_quality_summary(report)
    print(text)

    if args.write_report:
        output_paths = write_data_quality_report(PROJECT_ROOT, report, config=config)
        for p in output_paths:
            print(f"Written: {p}")
        print("")

    if report.status == "BLOCKED":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
