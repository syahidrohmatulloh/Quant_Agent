#!/usr/bin/env python3
"""CLI: python tools/run_runtime_smoke_test.py"""
import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.smoke_test import run_smoke_test

if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "reports/smoke_test_result.json"
    result = run_smoke_test(output_path=output_path)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["status"] == "passed" else 1)
