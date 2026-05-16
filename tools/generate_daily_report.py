#!/usr/bin/env python3
"""CLI: python tools/generate_daily_report.py --session-dir reports/session_001 --output reports/session_001/daily_report.md"""
import os
import sys
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.session_report import DailyReportGenerator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate daily paper trading report.")
    parser.add_argument("--session-dir", required=True, help="Session output directory")
    parser.add_argument("--output", help="Report output path (default: session-dir/daily_report.md)")
    args = parser.parse_args()

    gen = DailyReportGenerator(args.session_dir, output_path=args.output)
    result = gen.generate()
    print(f"Report generated: {result['report_path']}")
