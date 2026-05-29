"""Show paper positions from state file.

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
    parser = argparse.ArgumentParser(description="Show paper positions.")
    parser.add_argument("--state", required=True, help="Path to position state JSON.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    with open(args.state, "r", encoding="utf-8") as f:
        data = json.load(f)

    positions = data.get("positions", {})
    print("Positions saved at: " + data.get("saved_at", "unknown"))
    print("Count: " + str(len(positions)))
    for key, pos in positions.items():
        print("  " + key + " | " + pos.get("side", "FLAT") + " | qty=" + str(pos.get("quantity", 0))
        + " | avg=" + str(pos.get("average_price", 0)) + " | realized=" + str(pos.get("realized_pnl", 0))
        + " | unrealized=" + str(pos.get("unrealized_pnl", 0)))


if __name__ == "__main__":
    main()
