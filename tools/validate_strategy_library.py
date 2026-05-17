#!/usr/bin/env python3
"""
CLI tool to validate the strategy library (registry, configs, signals).
Safe by default. No credentials. No broker calls.
"""
import argparse
import json
import sys
sys.path.insert(0, ".")

from strategies.base import StrategyConfig
from strategy_lab.validation import validate_registry, validate_config, validate_signal_shape, validate_no_nan_inf


def _synthetic_data(symbols: list, bars: int = 50) -> dict:
    import random
    random.seed(42)
    from datetime import datetime
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


def _get_strategy_params(name: str) -> dict:
    """Return minimal valid params for each strategy to avoid errors."""
    params_map = {
        "pairs_trading": {"pair": ["EURUSD", "USDJPY"], "lookback": 10, "threshold": 1.0},
        "ensemble_selector": {
            "strategies": ["time_series_momentum", "ma_crossover"],
            "method": "vote",
            "time_series_momentum": {"lookback": 5, "threshold": 0.001},
            "ma_crossover": {"fast": 3, "slow": 10}
        },
    }
    return params_map.get(name, {})


def main():
    parser = argparse.ArgumentParser(description="Validate strategy library")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    print("PAPER-ONLY DISCLAIMER: Validation is for research/educational purposes only.")

    registry_result = validate_registry()
    all_ok = all(v["status"] == "ok" for v in registry_result.values())

    # Quick signal sanity on each strategy
    from strategies.registry import StrategyRegistry
    data = _synthetic_data(["EURUSD", "USDJPY"], bars=60)
    signal_errors = {}
    for name in StrategyRegistry.list_strategies():
        try:
            cls = StrategyRegistry.get(name)
            params = _get_strategy_params(name)
            cfg = StrategyConfig(name=name, symbols=["EURUSD", "USDJPY"], params=params)
            instance = cls(cfg)
            result = instance.generate(data)
            errs = validate_signal_shape(result, ["EURUSD", "USDJPY"])
            errs += validate_no_nan_inf(result)
            signal_errors[name] = errs
        except Exception as e:
            signal_errors[name] = [str(e)]

    out = {
        "registry_valid": all_ok,
        "registry_details": registry_result,
        "signal_errors": signal_errors,
        "overall_ok": all_ok and all(not v for v in signal_errors.values())
    }
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print("Saved to " + args.output)
    else:
        print(json.dumps(out, indent=2))
    sys.exit(0 if out["overall_ok"] else 1)


if __name__ == "__main__":
    main()
