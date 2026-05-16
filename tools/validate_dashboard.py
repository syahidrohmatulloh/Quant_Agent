#!/usr/bin/env python3
"""CLI: python tools/validate_dashboard.py --base-url http://127.0.0.1:8000 --viewer-token viewer123"""
import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.dashboard_validator import DashboardValidator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate dashboard routes and security.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Dashboard base URL")
    parser.add_argument("--viewer-token", default=None, help="Viewer token")
    parser.add_argument("--in-process", action="store_true", help="Use in-process TestClient")
    args = parser.parse_args()

    if args.in_process:
        from main import app
        validator = DashboardValidator(app=app, viewer_token=args.viewer_token)
    else:
        validator = DashboardValidator(base_url=args.base_url, viewer_token=args.viewer_token)
    result = validator.validate()
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["valid"] else 1)
