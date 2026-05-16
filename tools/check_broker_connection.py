#!/usr/bin/env python3
"""Check broker connection and health."""
import argparse
import json
import sys

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
    parser = argparse.ArgumentParser(description="Check broker connection")
    parser.add_argument("--config", required=True, help="Path to broker config JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    broker_name = cfg.get("broker_name", "unknown")
    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({
            "broker": broker_name,
            "environment": cfg.get("environment", "unknown"),
            "healthy": False,
            "reason": str(e),
            "paper_only": True,
        }, indent=2))
        sys.exit(1)

    adapter_cls = ADAPTERS.get(broker_name)
    if adapter_cls is None:
        print(json.dumps({
            "broker": broker_name,
            "environment": config.environment,
            "healthy": False,
            "reason": "unsupported_broker",
            "paper_only": True,
        }, indent=2))
        sys.exit(1)

    adapter = adapter_cls(config)
    health = adapter.health_check()
    output = {
        "broker": broker_name,
        "environment": config.environment,
        "healthy": health.get("healthy", False),
        "reason": health.get("reason", ""),
        "paper_only": True,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
