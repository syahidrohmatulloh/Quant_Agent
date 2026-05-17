#!/usr/bin/env python3
"""
CLI tool: fetch MT5 OHLCV and run a Phase 10 strategy signal.
Data-only. Paper-only. No live trading. No order submission.
"""
import argparse
import sys
import json

sys.path.insert(0, ".")

from broker_integration.mt5.mt5_market_data import MT5MarketData
from broker_integration.mt5.mt5_adapter import MT5StrategyAdapter
from broker_integration.mt5.mt5_errors import MT5Error
from strategies.registry import StrategyRegistry
from strategies.base import StrategyConfig

PAPER_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def main():
    parser = argparse.ArgumentParser(description="Fetch MT5 data and run strategy signal")
    parser.add_argument("--strategy", required=True, help="Strategy name from registry")
    parser.add_argument("--symbol", required=True, help="MT5 symbol (e.g., EURUSD)")
    parser.add_argument("--timeframe", default="H1", help="Timeframe: M1,M5,M15,M30,H1,H4,D1")
    parser.add_argument("--count", type=int, default=100, help="Number of bars to fetch")
    parser.add_argument("--params", default="{}", help="JSON strategy params")
    parser.add_argument("--output", default=None, help="Output JSON file")
    parser.add_argument("--timeout", type=int, default=60000, help="MT5 init timeout ms")
    args = parser.parse_args()

    print(PAPER_DISCLAIMER)
    print()

    params = json.loads(args.params)
    client = MT5MarketData(config={"timeout": args.timeout})
    try:
        client.initialize()
        adapter = MT5StrategyAdapter(client)
        data = adapter.fetch_for_strategy([args.symbol], args.timeframe, args.count)

        cfg = StrategyConfig(name=args.strategy, symbols=[args.symbol], params=params)
        cls = StrategyRegistry.get(args.strategy)
        strategy = cls(cfg)
        result = strategy.generate(data)

        out = {
            "strategy": args.strategy,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "bars_fetched": len(data.get(args.symbol, [])),
            "disclaimer": result.disclaimer,
            "signals": [
                {"timestamp": str(s.timestamp), "symbol": s.symbol, "signal": s.signal,
                 "weight": s.weight, "meta": s.meta} for s in result.signals
            ],
            "metrics": result.metrics,
        }
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, default=str)
            print("Saved to " + args.output)
        else:
            print(json.dumps(out, indent=2, default=str))
    except MT5Error as e:
        print("[ERROR] " + str(e))
        sys.exit(1)
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
