#!/usr/bin/env python3
"""Diagnose OANDA practice connectivity."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_http_transport import OandaHttpTransport


def main():
    parser = argparse.ArgumentParser(description="Diagnose OANDA practice connection")
    parser.add_argument("--config", required=True, help="Path to OANDA config JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({
            "broker": "oanda",
            "environment": cfg.get("environment", "unknown"),
            "healthy": False,
            "reason": str(e),
            "paper_only": True,
            "live_trading_enabled": False,
        }, indent=2))
        sys.exit(1)

    try:
        transport = OandaHttpTransport(config)
    except Exception as e:
        print(json.dumps({
            "broker": "oanda",
            "environment": config.environment,
            "healthy": False,
            "reason": f"transport_init_error: {e}",
            "paper_only": True,
            "live_trading_enabled": False,
        }, indent=2))
        sys.exit(1)

    health = transport.health_check()
    output = {
        "broker": "oanda",
        "environment": config.environment,
        "healthy": health.get("healthy", False),
        "reason": health.get("reason", ""),
        "paper_only": True,
        "live_trading_enabled": False,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
