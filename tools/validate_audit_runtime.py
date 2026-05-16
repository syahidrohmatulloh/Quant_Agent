#!/usr/bin/env python3
"""CLI: python tools/validate_audit_runtime.py --audit-path data/audit.jsonl --db-path data/quant_platform.db"""
import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.audit_validator import AuditRuntimeValidator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate audit trail at runtime.")
    parser.add_argument("--audit-path", default="./data/audit.jsonl", help="Path to audit JSONL")
    parser.add_argument("--db-path", default="./data/quant_platform.db", help="Path to SQLite DB")
    args = parser.parse_args()

    validator = AuditRuntimeValidator(args.audit_path, args.db_path)
    result = validator.validate()
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["valid"] else 1)
