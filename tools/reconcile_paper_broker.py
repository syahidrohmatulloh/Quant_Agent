#!/usr/bin/env python3
"""Reconcile internal paper state with broker snapshot."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_runtime.broker_reconciliation import BrokerReconciliation


def main():
    parser = argparse.ArgumentParser(description="Reconcile paper broker")
    parser.add_argument("--internal", required=True, help="Internal state JSON")
    parser.add_argument("--broker", required=True, help="Broker snapshot JSON")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    with open(args.internal) as f:
        internal = json.load(f)
    with open(args.broker) as f:
        broker = json.load(f)

    rec = BrokerReconciliation()
    result = rec.reconcile(internal, broker)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
