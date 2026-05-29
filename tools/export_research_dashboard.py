#!/usr/bin/env python3
"""Export research dashboard JSON.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    results_dir = Path(args.results_dir)
    files = sorted(results_dir.glob("*.json"))
    if not files:
        print("No JSON results found.")
        sys.exit(1)

    # Use the latest report
    latest = files[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Dashboard JSON exported to {args.output}")


if __name__ == "__main__":
    main()
