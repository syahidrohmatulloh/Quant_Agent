
import os
import tempfile
import pytest
from storage.audit import AuditLogger
from storage.db import SQLiteStore

def test_audit_and_db_together():
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = os.path.join(tmpdir, "audit.jsonl")
        db_path = os.path.join(tmpdir, "test.db")
        logger = AuditLogger(audit_path)
        store = SQLiteStore(db_path)
        order = {
            "order_id": "o1", "request_id": "r1", "idempotency_key": "key1",
            "signal_id": None, "strategy_id": None, "strategy_version": None,
            "model_version": None, "source": "manual", "symbol": "EURUSD",
            "direction": "buy", "volume": 1.0, "entry_price": 1.1,
            "sl": None, "tp": None, "status": "open",
            "broker_order_id": "b1", "broker_position_id": "p1",
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"
        }
        store.insert_order(order)
        r = logger.log("order_created", "r1", "admin", "admin", {"order_id": "o1"})
        assert r["event_sequence"] == 1
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT order_id FROM orders")
            assert cur.fetchone()[0] == "o1"
