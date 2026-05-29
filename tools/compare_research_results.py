#!/usr/bin/env python3
"""Compare research results from reports/research_analytics.

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
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    results_dir = Path(args.results_dir)
    files = sorted(results_dir.glob("*.json"))
    summaries = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            summaries.append({
                "file": str(f.name),
                "name": data.get("name", "N/A"),
                "generated_at": data.get("generated_at", "N/A"),
                "paper_only": data.get("paper_only", True),
                "data_only": data.get("data_only", True),
                "no_order_submission": data.get("no_order_submission", True),
            })
        except Exception:
            pass

    print(json.dumps({"compared": len(summaries), "results": summaries}, indent=2))


if __name__ == "__main__":
    main()
