#!/usr/bin/env python3
"""Record market data sample from broker adapter."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_practice_adapter import OandaPracticeAdapter
from broker_integration.alpaca.alpaca_paper_adapter import AlpacaPaperAdapter
from broker_integration.ibkr.ibkr_paper_adapter import IbkrPaperAdapter

ADAPTERS = {
    "oanda": OandaPracticeAdapter,
    "alpaca": AlpacaPaperAdapter,
    "ibkr": IbkrPaperAdapter,
}


def main():
    parser = argparse.ArgumentParser(description="Record market data sample")
    parser.add_argument("--config", required=True, help="Broker config JSON")
    parser.add_argument("--symbol", required=True, help="Symbol to sample")
    parser.add_argument("--count", type=int, default=10, help="Number of samples")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    broker_name = cfg.get("broker_name", "unknown")
    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    adapter_cls = ADAPTERS.get(broker_name)
    if adapter_cls is None:
        print(json.dumps({"error": "unsupported_broker"}))
        sys.exit(1)

    adapter = adapter_cls(config)
    health = adapter.health_check()
    if not health.get("healthy"):
        print(json.dumps({"error": health.get("reason", "unhealthy")}))
        sys.exit(1)

    samples = []
    for _ in range(args.count):
        tick = adapter.get_latest_tick(args.symbol)
        if tick:
            samples.append(tick)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({"symbol": args.symbol, "samples": samples}, f, indent=2)

    print(f"Recorded {len(samples)} samples to {args.output}")


if __name__ == "__main__":
    main()
