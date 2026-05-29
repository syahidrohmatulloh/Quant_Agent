#!/usr/bin/env python3
"""CLI: Show current paper portfolio state.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from paper_orchestration.paper_portfolio import PaperPortfolio


def main():
    parser = argparse.ArgumentParser(description="Show paper portfolio state.")
    parser.add_argument("--state", required=True, help="Path to portfolio state JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    portfolio = PaperPortfolio(state_path=args.state)
    state = portfolio.get_state()
    print(json.dumps(state, indent=2, default=str))


if __name__ == "__main__":
    main()
