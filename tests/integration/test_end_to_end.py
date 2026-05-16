
import os
import tempfile
import pytest
from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.db import SQLiteStore
from storage.audit import AuditLogger

def test_end_to_end_order():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        audit_path = os.path.join(tmpdir, "audit.jsonl")
        broker = PaperBroker(balance=100000)
        store = SQLiteStore(db_path)
        logger = AuditLogger(audit_path)
        rm = RiskManager()

        decision = rm.evaluate("EURUSD", "buy", 1.0)
        assert decision.allowed

        oid, pid = broker.open_position("EURUSD", "buy", 1.0, 1.1000)
        assert oid.startswith("PAPER")

        logger.log("order", "r1", "admin", "admin", {"oid": oid})

        order = {
            "order_id": "o1", "request_id": "r1", "idempotency_key": "k1",
            "signal_id": None, "strategy_id": None, "strategy_version": None,
            "model_version": None, "source": "manual", "symbol": "EURUSD",
            "direction": "buy", "volume": 1.0, "entry_price": 1.1,
            "sl": None, "tp": None, "status": "open",
            "broker_order_id": oid, "broker_position_id": pid,
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"
        }
        store.insert_order(order)

        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT count(*) FROM orders")
            assert cur.fetchone()[0] == 1
