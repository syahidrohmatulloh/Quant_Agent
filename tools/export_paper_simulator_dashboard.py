"""Export paper simulator dashboard JSON.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_simulator.position_book import PositionBook
from paper_simulator.dashboard_export import export_dashboard_json


def main():
    parser = argparse.ArgumentParser(description="Export paper simulator dashboard JSON.")
    parser.add_argument("--state", required=True, help="Path to position state JSON.")
    parser.add_argument("--output", required=True, help="Path to output dashboard JSON.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    book = PositionBook(args.state)
    config = {
        "name": "paper_simulator_dashboard_export",
        "initial_cash": 100000.0,
        "base_currency": "USD",
    }

    export_dashboard_json(
        config=config,
        position_book=book,
        fills=[],
        pnl=None,
        exposure=None,
        warnings=[],
        errors=[],
        output_path=args.output,
    )
    print("Dashboard exported to: " + args.output)


if __name__ == "__main__":
    main()
