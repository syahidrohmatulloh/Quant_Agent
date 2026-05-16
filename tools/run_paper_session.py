#!/usr/bin/env python3
"""CLI: python tools/run_paper_session.py --data examples/replay_fx_sample.csv --config examples/paper_session_config.json --cycles 100 --output reports/session_001/"""
import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.paper_session import run_paper_session

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a paper trading session with replay data.")
    parser.add_argument("--data", required=True, help="Path to replay CSV file")
    parser.add_argument("--config", required=True, help="Path to paper session config JSON")
    parser.add_argument("--cycles", type=int, default=100, help="Max cycles to run")
    parser.add_argument("--output", default="reports/session_001", help="Output directory")
    args = parser.parse_args()

    result = run_paper_session(args.data, args.config, cycles=args.cycles, output_dir=args.output)
    print(json.dumps(result, indent=2, default=str))
    print(f"\nSession outputs written to: {args.output}")
