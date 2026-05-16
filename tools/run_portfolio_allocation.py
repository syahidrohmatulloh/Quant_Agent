
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from portfolio_optimization.allocation_engine import AllocationEngine
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals", required=True, help="JSON with signals")
    parser.add_argument("--prices", required=True, help="CSV with price history")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.signals, "r") as f:
        signals = json.load(f)
    returns = pd.read_csv(args.prices, index_col=0)

    engine = AllocationEngine()
    result = engine.allocate(signals, returns)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print("Allocation saved to", args.output)

if __name__ == "__main__":
    main()
