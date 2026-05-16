import os
import sys
import json
import pytest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.audit_validator import AuditRuntimeValidator
from storage.audit import AuditLogger


class TestAuditRuntimeValidator:
    def test_valid_audit_passes(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = os.path.join(td, "audit.jsonl")
            audit = AuditLogger(audit_path)
            audit.log("signal_generated", "req-1", "system", "system", {"signal": "buy"})
            audit.log("paper_order_created", "req-1", "system", "system", {"order_id": "O1"})
            validator = AuditRuntimeValidator(audit_path, os.path.join(td, "test.db"))
            result = validator.validate()
            assert result["valid"] is True
            assert result["events_checked"] == 2

    def test_missing_event_fails(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = os.path.join(td, "audit.jsonl")
            audit = AuditLogger(audit_path)
            audit.log("signal_generated", "req-1", "system", "system", {"signal": "buy"})
            # No follow-up order/rejection
            validator = AuditRuntimeValidator(audit_path, os.path.join(td, "test.db"))
            result = validator.validate()
            assert result["valid"] is False
            assert any("no follow-up" in e for e in result["errors"])

    def test_broken_chain_fails(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = os.path.join(td, "audit.jsonl")
            # Write malformed chain manually
            with open(audit_path, "w") as f:
                f.write(json.dumps({
                    "event_sequence": 1, "event_id": "e1", "event_type": "test",
                    "request_id": "r1", "actor": "sys", "role": "sys",
                    "payload_json": "{}", "payload_hash": "abcd",
                    "previous_event_hash": "NOT_GENESIS",
                    "event_hash": "hash1", "timestamp_utc": "2024-01-01T00:00:00+00:00"
                }) + "\n")
            validator = AuditRuntimeValidator(audit_path, os.path.join(td, "test.db"))
            result = validator.validate()
            assert result["valid"] is False
            assert any("GENESIS" in e for e in result["errors"])

    def test_live_execution_event_fails(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = os.path.join(td, "audit.jsonl")
            audit = AuditLogger(audit_path)
            audit.log("live_order_created", "req-1", "system", "system", {"broker": "live"})
            validator = AuditRuntimeValidator(audit_path, os.path.join(td, "test.db"))
            result = validator.validate()
            assert result["valid"] is False
            assert any("Live execution" in e for e in result["errors"])

    def test_rejection_without_reason_fails(self):
        with tempfile.TemporaryDirectory() as td:
            audit_path = os.path.join(td, "audit.jsonl")
            audit = AuditLogger(audit_path)
            audit.log("signal_rejected", "req-1", "system", "system", {"reason": ""})
            validator = AuditRuntimeValidator(audit_path, os.path.join(td, "test.db"))
            result = validator.validate()
            assert result["valid"] is False
            assert any("missing reason" in e for e in result["errors"])
