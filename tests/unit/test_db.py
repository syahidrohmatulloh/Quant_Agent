
import os
import sqlite3
import tempfile
import pytest
from storage.db import SQLiteStore

def test_insert_and_retrieve_order():
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
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT order_id FROM orders")
            rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "o1"

def test_insert_position():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = SQLiteStore(db_path)
        pos = {
            "position_id": "p1", "order_id": "o1", "symbol": "EURUSD",
            "direction": "buy", "volume": 1.0, "entry_price": 1.1,
            "current_price": 1.1, "sl": None, "tp": None, "status": "open",
            "broker_position_id": "bp1", "opened_at": "2024-01-01T00:00:00",
            "closed_at": None, "realized_pnl": None, "unrealized_pnl": None
        }
        store.insert_position(pos)
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT position_id FROM positions")
            rows = cur.fetchall()
        assert len(rows) == 1

def test_insert_risk_decision():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = SQLiteStore(db_path)
        dec = {
            "risk_decision_id": "rd1", "request_id": "r1", "order_id": "o1",
            "allowed": 1, "severity": "low", "reason": "ok",
            "checks_json": "{}", "timestamp_utc": "2024-01-01T00:00:00"
        }
        store.insert_risk_decision(dec)
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT risk_decision_id FROM risk_decisions")
            rows = cur.fetchall()
        assert len(rows) == 1
