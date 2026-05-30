#!/usr/bin/env python3
"""CLI: validate project documentation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from docs_tools.doc_validator import validate_docs


def main():
    parser = argparse.ArgumentParser(description="Validate project documentation")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This tool does not approve or enable live trading.")

    validator = validate_docs(PROJECT_ROOT)

    for p in validator.passes:
        print("PASS: " + p)
    for w in validator.warnings:
        print("WARN: " + w)
    for e in validator.errors:
        print("FAIL: " + e)

    if validator.errors:
        print("Docs validation FAILED.")
        sys.exit(1)
    elif validator.warnings:
        print("Docs validation PASSED with warnings.")
        sys.exit(0)
    else:
        print("Docs validation OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
