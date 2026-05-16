
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backtesting.data_feed import HistoricalDataFeed
from backtesting.backtest_engine import BacktestEngine
from backtesting.report import ReportGenerator
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

    feed = HistoricalDataFeed(data)
    strat_cls = STRATEGIES.get(config.get("strategy", "dummy"), DummyAlwaysBuy)
    strategy = strat_cls(**config.get("strategy_params", {}))
    engine = BacktestEngine(feed, strategy, **config.get("engine", {}))
    result = engine.run()

    os.makedirs(args.output, exist_ok=True)
    report = ReportGenerator(result)
    report.to_json(os.path.join(args.output, "report.json"))
    report.to_markdown(os.path.join(args.output, "report.md"))
    report.to_csv(os.path.join(args.output, "trades.csv"))
    print("Backtest complete. Reports saved to", args.output)

if __name__ == "__main__":
    main()
