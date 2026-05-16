#!/usr/bin/env python3
"""Fetch OANDA practice account snapshot."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_practice_snapshot import OandaPracticeSnapshot
from broker_integration.oanda.oanda_http_transport import OandaHttpTransport


def main():
    parser = argparse.ArgumentParser(description="Fetch OANDA practice snapshot")
    parser.add_argument("--config", required=True, help="OANDA config JSON")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    transport = OandaHttpTransport(config)
    snapshot = OandaPracticeSnapshot(config, transport)
    result = snapshot.fetch()

    if result is None:
        print(json.dumps({"error": "snapshot_unavailable", "reason": "missing_credentials_or_transport"}))
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Snapshot saved to {args.output}")


if __name__ == "__main__":
    main()
