#!/usr/bin/env python3
"""Dry-run OANDA practice order."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_practice_orders import OandaPracticeOrderClient


def main():
    parser = argparse.ArgumentParser(description="Dry-run OANDA paper order")
    parser.add_argument("--config", required=True, help="OANDA config JSON")
    parser.add_argument("--symbol", required=True, help="Instrument symbol")
    parser.add_argument("--units", type=float, required=True, help="Order units")
    parser.add_argument("--side", required=True, choices=["buy", "sell"], help="Order side")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    parser.add_argument("--submit-practice-order", action="store_true", help="Actually submit to practice (requires allow_order_submission)")
    parser.add_argument("--model-id", default="", help="Model ID for audit")
    parser.add_argument("--signal-id", default="", help="Signal ID for audit")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if args.submit_practice_order:
        # Override dry_run
        args.dry_run = False
        if not config.allow_order_submission:
            print(json.dumps({
                "error": "order_submission_disabled",
                "message": "Set allow_order_submission=true in config to submit practice orders",
                "paper_only": True,
            }))
            sys.exit(1)

    client = OandaPracticeOrderClient(config)
    result = client.submit_order(
        symbol=args.symbol,
        side=args.side,
        units=args.units,
        dry_run=args.dry_run,
        model_id=args.model_id,
        signal_id=args.signal_id,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
