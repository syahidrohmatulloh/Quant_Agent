#!/usr/bin/env python3
"""
Run the Phase 14 local dashboard server.
Default host 127.0.0.1. No broker calls. No credentials.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import uvicorn
except ImportError as e:
    print("Error: uvicorn is required. Install with: pip install uvicorn")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run Quant_Agent Phase 14 local dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    if args.host != "127.0.0.1":
        print(f"WARNING: Binding to {args.host} instead of 127.0.0.1. Ensure this is intentional.")

    print("=" * 60)
    print("Quant_Agent Local Dashboard (Phase 14)")
    print("=" * 60)
    print(f"URL: http://{args.host}:{args.port}")
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    uvicorn.run("dashboard.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
