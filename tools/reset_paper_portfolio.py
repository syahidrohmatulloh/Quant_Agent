#!/usr/bin/env python3
"""CLI: Reset paper portfolio state.
Requires explicit --confirm-reset.
Paper-only. No live trading.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from paper_orchestration.paper_portfolio import PaperPortfolio


def main():
    parser = argparse.ArgumentParser(description="Reset paper portfolio state.")
    parser.add_argument("--state", required=True, help="Path to portfolio state JSON")
    parser.add_argument("--confirm-reset", action="store_true", required=True, help="Confirm reset")
    args = parser.parse_args()

    print("=" * 60)
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("=" * 60)

    portfolio = PaperPortfolio(state_path=args.state)
    portfolio.reset(confirm=args.confirm_reset)
    print("Portfolio state reset.")


if __name__ == "__main__":
    main()
