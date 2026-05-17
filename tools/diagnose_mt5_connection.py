#!/usr/bin/env python3
"""
CLI tool to diagnose MT5 terminal/module availability.
Data-only. No order execution. No live trading.
"""
import argparse
import sys

sys.path.insert(0, ".")

PAPER_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def main():
    parser = argparse.ArgumentParser(description="Diagnose MT5 terminal availability")
    parser.add_argument("--timeout", type=int, default=60000, help="MT5 init timeout ms")
    args = parser.parse_args()

    print(PAPER_DISCLAIMER)
    print()

    # Check if MetaTrader5 package is installed
    try:
        import MetaTrader5 as mt5
        print("[OK] MetaTrader5 Python package is installed")
    except ImportError:
        print("[FAIL] MetaTrader5 Python package is NOT installed")
        print("       Install: pip install MetaTrader5")
        sys.exit(1)

    # Try to initialize
    try:
        ok = mt5.initialize(timeout=args.timeout)
        if not ok:
            err = mt5.last_error()
            print(f"[FAIL] MT5 terminal initialization failed: {err}")
            sys.exit(1)
        print("[OK] MT5 terminal initialized")
    except Exception as e:
        print(f"[FAIL] MT5 initialization exception: {e}")
        sys.exit(1)

    # Check visible symbols
    try:
        symbols = mt5.symbols_get()
        if symbols:
            print(f"[OK] {len(symbols)} symbols visible in Market Watch")
            # Print first 10
            for s in symbols[:10]:
                print(f"       - {s.name}")
        else:
            print("[WARN] No symbols visible in Market Watch")
    except Exception as e:
        print(f"[WARN] Could not retrieve symbols: {e}")

    mt5.shutdown()
    print("[OK] MT5 shutdown complete")
    print()
    print("Diagnosis complete. Terminal is reachable for market data.")


if __name__ == "__main__":
    main()
