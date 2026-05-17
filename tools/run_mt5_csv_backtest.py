#!/usr/bin/env python3
"""
CLI tool: load MT5 CSV OHLCV and run a Phase 10 strategy backtest.
No MetaTrader5 package required. Paper-only. No live trading.
"""
import argparse
import sys
import json

sys.path.insert(0, ".")

from broker_integration.mt5.mt5_csv_loader import load_mt5_csv_multi
from strategies.registry import StrategyRegistry
from strategies.base import StrategyConfig
from strategy_lab.backtest import SimpleBacktestEngine

PAPER_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def main():
    parser = argparse.ArgumentParser(description="Load MT5 CSV and run backtest")
    parser.add_argument("--csv", required=True, help="Path to MT5 OHLCV CSV")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--symbol", default=None, help="Symbol override")
    parser.add_argument("--timeframe", default=None, help="Timeframe override")
    parser.add_argument("--params", default="{}", help="JSON strategy params")
    parser.add_argument("--initial", type=float, default=100000.0, help="Initial balance")
    parser.add_argument("--output", default=None, help="Output JSON file")
    args = parser.parse_args()

    print(PAPER_DISCLAIMER)
    print()

    params = json.loads(args.params)
    try:
        data = load_mt5_csv_multi(args.csv, symbol=args.symbol, timeframe=args.timeframe)
        symbols = list(data.keys())
        cfg = StrategyConfig(name=args.strategy, symbols=symbols, params=params)
        cls = StrategyRegistry.get(args.strategy)
        strategy = cls(cfg)

        # Convert to strategy_lab format (needs volume key)
        bt_data = {}
        for sym, bars in data.items():
            clean = []
            for b in bars:
                clean.append({
                    "timestamp": b["timestamp"],
                    "open": b["open"],
                    "high": b["high"],
                    "low": b["low"],
                    "close": b["close"],
                    "volume": b["tick_volume"],
                })
            bt_data[sym] = clean

        engine = SimpleBacktestEngine(bt_data, strategy, initial_balance=args.initial)
        result = engine.run()

        out = {
            "strategy": args.strategy,
            "source": args.csv,
            "symbols": symbols,
            "initial_balance": args.initial,
            "disclaimer": "PAPER-ONLY / DATA-ONLY. No live trading.",
            "result": result,
        }
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, default=str)
            print("Saved to " + args.output)
        else:
            print(json.dumps(out, indent=2, default=str))
    except Exception as e:
        print("[ERROR] " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
