
import os
import json
import tempfile
import pytest
from storage.audit import AuditLogger

def test_audit_log_chain():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        logger = AuditLogger(path)
        r1 = logger.log("test_event", "req-1", "admin", "admin", {"a": 1})
        r2 = logger.log("test_event", "req-2", "admin", "admin", {"b": 2})
        assert r1["event_sequence"] == 1
        assert r2["event_sequence"] == 2
        assert r2["previous_event_hash"] == r1["event_hash"]
        with open(path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2

def test_audit_payload_hash():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        logger = AuditLogger(path)
        r = logger.log("test", "req-1", "admin", "admin", {"x": 1})
        assert r["payload_hash"]
        assert r["event_hash"]

def test_audit_genesis_first():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        logger = AuditLogger(path)
        r = logger.log("test", "req-1", "admin", "admin", {})
        assert r["previous_event_hash"] == "GENESIS"
