#!/usr/bin/env python3
"""Diagnose market data sample for quality issues."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Diagnose market data")
    parser.add_argument("--input", required=True, help="Market data sample JSON")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    samples = data.get("samples", [])
    issues = []
    for i, tick in enumerate(samples):
        if not tick.get("bid") or not tick.get("ask"):
            issues.append({"index": i, "issue": "missing_price"})
        spread = tick.get("spread", 0)
        if spread > 0.01:
            issues.append({"index": i, "issue": "wide_spread", "spread": spread})
        if tick.get("source") not in {"oanda_practice", "alpaca_paper", "ibkr_paper"}:
            issues.append({"index": i, "issue": "unexpected_source", "source": tick.get("source")})

    report = {
        "total_samples": len(samples),
        "issues_found": len(issues),
        "issues": issues,
        "status": "ok" if not issues else "warning",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
