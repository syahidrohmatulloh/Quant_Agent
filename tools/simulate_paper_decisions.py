"""Simulate paper decisions through the fill model.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_simulator.simulator_config import load_simulator_config
from paper_simulator.order_intent import build_order_intents
from paper_simulator.fill_model import simulate_fill
from paper_simulator.price_loader import PriceLoader


def main():
    parser = argparse.ArgumentParser(description="Simulate paper decisions.")
    parser.add_argument("--decisions", required=True, help="Path to decisions JSONL.")
    parser.add_argument("--config", required=True, help="Path to simulator config JSON.")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV paths.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    config, ok, errors, warnings = load_simulator_config(args.config)
    if not ok:
        print("Config validation FAILED:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)

    decisions = []
    with open(args.decisions, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                decisions.append(json.loads(line))

    risk_config = config.get("risk", {})
    initial_cash = config.get("initial_cash", 100000.0)
    intents = build_order_intents(decisions, risk_config, initial_cash)

    costs_config = config.get("costs", {})
    fills = []
    for intent in intents:
        if intent.side in ("HOLD", "REJECTED"):
            continue
        sym_cfg = None
        for sym in config.get("symbols", []):
            if sym.get("symbol") == intent.symbol:
                sym_cfg = sym
                break
        if sym_cfg is None:
            print("WARN: No symbol config for " + intent.symbol)
            continue
        try:
            loader = PriceLoader(sym_cfg["csv"], symbol=intent.symbol, timeframe=intent.timeframe)
            price = loader.latest_close()
        except Exception as e:
            print("WARN: Price load failed for " + intent.symbol + ": " + str(e))
            continue
        fill = simulate_fill(intent, price, costs_config, sym_cfg)
        if fill:
            fills.append(fill.to_dict())
            print("FILL: " + fill.fill_id + " | " + fill.symbol + " | " + fill.side + " | " + str(fill.fill_price))

    print("Simulated " + str(len(fills)) + " fills.")


if __name__ == "__main__":
    main()
