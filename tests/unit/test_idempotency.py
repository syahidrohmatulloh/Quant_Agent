
import os
import tempfile
import pytest
from storage.db import SQLiteStore

def test_idempotency_key_unique():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
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
        with pytest.raises(Exception):
            store.insert_order(order)

def test_different_idempotency_keys():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = SQLiteStore(db_path)
        for i in range(3):
            order = {
                "order_id": f"o{i}", "request_id": f"r{i}", "idempotency_key": f"key{i}",
                "signal_id": None, "strategy_id": None, "strategy_version": None,
                "model_version": None, "source": "manual", "symbol": "EURUSD",
                "direction": "buy", "volume": 1.0, "entry_price": 1.1,
                "sl": None, "tp": None, "status": "open",
                "broker_order_id": f"b{i}", "broker_position_id": f"p{i}",
                "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"
            }
            store.insert_order(order)
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT count(*) FROM orders")
            assert cur.fetchone()[0] == 3
