#!/usr/bin/env python3
"""
CLI tool to run a simple backtest on synthetic or CSV data.
Safe by default. No credentials. No broker calls.
"""
import argparse
import csv
import json
import sys
from datetime import datetime
sys.path.insert(0, ".")

from strategies.registry import StrategyRegistry
from strategies.base import StrategyConfig
from strategy_lab.backtest import SimpleBacktestEngine


def _load_csv(path: str) -> dict:
    data = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get("symbol", "UNKNOWN")
            data.setdefault(sym, []).append({
                "timestamp": row.get("timestamp", datetime.now().isoformat()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0))
            })
    return data


def _synthetic_data(symbols: list, bars: int = 100) -> dict:
    import random
    random.seed(42)
    data = {}
    for sym in symbols:
        price = 1.1000
        rows = []
        for i in range(bars):
            noise = random.uniform(-0.005, 0.005)
            o = price
            c = price + noise
            h = max(o, c) + random.uniform(0, 0.002)
            l = min(o, c) - random.uniform(0, 0.002)
            rows.append({
                "timestamp": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
                "open": round(o, 5),
                "high": round(h, 5),
                "low": round(l, 5),
                "close": round(c, 5),
                "volume": 1000.0
            })
            price = c
        data[sym] = rows
    return data


def main():
    parser = argparse.ArgumentParser(description="Run strategy backtest")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--symbols", default="EURUSD,USDJPY", help="Comma-separated symbols")
    parser.add_argument("--csv", default=None, help="CSV data path")
    parser.add_argument("--params", default="{}", help="JSON params")
    parser.add_argument("--initial", type=float, default=100000.0, help="Initial balance")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    print("PAPER-ONLY DISCLAIMER: Backtest results are for research only. No live trading.")

    symbols = [s.strip() for s in args.symbols.split(",")]
    data = _load_csv(args.csv) if args.csv else _synthetic_data(symbols)
    params = json.loads(args.params)
    cfg = StrategyConfig(name=args.strategy, symbols=symbols, params=params)
    cls = StrategyRegistry.get(args.strategy)
    strategy = cls(cfg)
    engine = SimpleBacktestEngine(data, strategy, initial_balance=args.initial)
    result = engine.run()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
