
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backtesting.walk_forward import WalkForward
from research.example_strategies import DummyAlwaysBuy, MACrossStrategy, BreakoutStrategy

STRATEGIES = {
    "dummy": DummyAlwaysBuy,
    "ma_cross": MACrossStrategy,
    "breakout": BreakoutStrategy
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)
    with open(args.data, "r") as f:
        data = json.load(f)

    strat_cls = STRATEGIES.get(config.get("strategy", "dummy"), DummyAlwaysBuy)
    wf = WalkForward(data, lambda: strat_cls(**config.get("strategy_params", {})), n_folds=config.get("n_folds", 5))
    results = wf.run()

    os.makedirs(args.output, exist_ok=True)
    with open(os.path.join(args.output, "walk_forward.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Walk-forward complete. Results saved to", args.output)

if __name__ == "__main__":
    main()
