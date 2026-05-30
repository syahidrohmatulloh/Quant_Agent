#!/usr/bin/env python3
"""CLI: show demo script.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Show demo script")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    demo_path = PROJECT_ROOT / "docs" / "DEMO_SCRIPT.md"
    if not demo_path.exists():
        print("FAIL: docs/DEMO_SCRIPT.md not found")
        sys.exit(1)

    content = demo_path.read_text(encoding="utf-8")

    if args.summary:
        print("Demo Script Summary")
        print("=" * 40)
        # Extract section headers
        for line in content.splitlines():
            if line.startswith("## ") or line.startswith("### "):
                print(line.lstrip("# "))
    else:
        print(content)

    sys.exit(0)


if __name__ == "__main__":
    main()
