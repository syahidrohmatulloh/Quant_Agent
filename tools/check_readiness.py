#!/usr/bin/env python3
"""CLI: python tools/check_readiness.py"""
import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.readiness_check import check_readiness

if __name__ == "__main__":
    result = check_readiness(project_root=PROJECT_ROOT)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["ready_for_paper_runtime"] else 1)
