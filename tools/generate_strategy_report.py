#!/usr/bin/env python3
"""
CLI tool to generate a strategy report (JSON or Markdown).
Safe by default. No credentials. No broker calls.
"""
import argparse
import json
import sys
sys.path.insert(0, ".")

from strategy_lab.reporting import StrategyReportGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate strategy report")
    parser.add_argument("--result", required=True, help="Path to JSON result file from backtest or walk-forward")
    parser.add_argument("--config", default="{}", help="JSON string of config metadata")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output_dir", default="reports", help="Output directory")
    args = parser.parse_args()

    print("PAPER-ONLY DISCLAIMER: Report is for educational/research purposes only.")

    with open(args.result, "r", encoding="utf-8") as f:
        result = json.load(f)
    config = json.loads(args.config)
    gen = StrategyReportGenerator(result, config, output_dir=args.output_dir)
    if args.format == "json":
        path = gen.to_json()
    else:
        path = gen.to_markdown()
    print(f"Report saved to: {path}")


if __name__ == "__main__":
    main()
