#!/usr/bin/env python3
"""
CLI tool to list all registered strategies.
Safe by default. No credentials. No broker calls.
"""
import argparse
import sys
sys.path.insert(0, ".")

from strategies.registry import StrategyRegistry


def main():
    parser = argparse.ArgumentParser(description="List registered quant strategies")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    names = StrategyRegistry.list_strategies()
    if args.format == "json":
        import json
        print(json.dumps({"strategies": names, "count": len(names)}, indent=2))
    else:
        print("Registered Strategies (paper-only / educational):")
        for n in names:
            print("  - " + n)
        print("")
        total_str = "Total: " + str(len(names))
        print(total_str)


if __name__ == "__main__":
    main()
