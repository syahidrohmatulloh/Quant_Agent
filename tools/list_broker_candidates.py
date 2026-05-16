#!/usr/bin/env python3
"""List broker candidates for a given country."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.indonesia.local_broker_catalog import list_local_brokers
from broker_integration.regional.regional_broker_catalog import list_regional_brokers


def main():
    parser = argparse.ArgumentParser(description="List broker candidates")
    parser.add_argument("--country", default="Indonesia", help="Target country")
    parser.add_argument("--require-demo", action="store_true", help="Require demo account")
    parser.add_argument("--require-api", action="store_true", help="Require API support")
    parser.add_argument("--asset-class", default="", help="Asset class filter")
    args = parser.parse_args()

    local = list_local_brokers()
    regional = list_regional_brokers()

    all_candidates = []
    for b in local:
        b["category"] = "indonesia_local"
        all_candidates.append(b)
    for b in regional:
        b["category"] = b.get("category", "regional")
        all_candidates.append(b)

    # Filter
    filtered = []
    for c in all_candidates:
        if args.require_demo and c.get("supports_demo_account") not in (True, "true", "verify"):
            continue
        if args.require_api and c.get("supports_api") not in (True, "true", "verify"):
            continue
        filtered.append({
            "broker_id": c["broker_id"],
            "display_name": c["display_name"],
            "category": c["category"],
            "supports_indonesian_residents": c.get("supports_indonesian_residents", "unknown_or_verify"),
            "supports_demo_account": c.get("supports_demo_account", "unknown"),
            "supports_api": c.get("supports_api", "unknown"),
            "integration_status": c.get("integration_status", "mock_only"),
            "live_trading_enabled": False,
        })

    # Sort: paper/demo + API first
    def rank(c):
        score = 0
        if c["supports_demo_account"] in (True, "true", "verify"):
            score += 2
        if c["supports_api"] in (True, "true", "verify"):
            score += 2
        if c["integration_status"] in ("api_possible", "mt5_demo_possible"):
            score += 1
        return score

    filtered.sort(key=rank, reverse=True)

    output = {
        "country": args.country,
        "paper_only": True,
        "candidates": filtered,
        "disclaimer": "Candidates require manual verification. This tool does not approve live trading.",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
