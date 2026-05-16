
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class SQLiteStore:
    def __init__(self, path: str = "./data/quant_platform.db"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._init_tables()

    def _connect(self):
        return sqlite3.connect(self.path, check_same_thread=False)

    def _init_tables(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    request_id TEXT,
                    idempotency_key TEXT UNIQUE,
                    signal_id TEXT,
                    strategy_id TEXT,
                    strategy_version TEXT,
                    model_version TEXT,
                    source TEXT,
                    symbol TEXT,
                    direction TEXT,
                    volume REAL,
                    entry_price REAL,
                    sl REAL,
                    tp REAL,
                    status TEXT,
                    broker_order_id TEXT,
                    broker_position_id TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    position_id TEXT PRIMARY KEY,
                    order_id TEXT,
                    symbol TEXT,
                    direction TEXT,
                    volume REAL,
                    entry_price REAL,
                    current_price REAL,
                    sl REAL,
                    tp REAL,
                    status TEXT,
                    broker_position_id TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    realized_pnl REAL,
                    unrealized_pnl REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_decisions (
                    risk_decision_id TEXT PRIMARY KEY,
                    request_id TEXT,
                    order_id TEXT,
                    allowed INTEGER,
                    severity TEXT,
                    reason TEXT,
                    checks_json TEXT,
                    timestamp_utc TEXT
                )
            """)

    def insert_order(self, order: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO orders VALUES (
                    :order_id, :request_id, :idempotency_key, :signal_id,
                    :strategy_id, :strategy_version, :model_version, :source,
                    :symbol, :direction, :volume, :entry_price, :sl, :tp,
                    :status, :broker_order_id, :broker_position_id,
                    :created_at, :updated_at
                )
            """, order)

    def insert_position(self, position: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO positions VALUES (
                    :position_id, :order_id, :symbol, :direction, :volume,
                    :entry_price, :current_price, :sl, :tp, :status,
                    :broker_position_id, :opened_at, :closed_at,
                    :realized_pnl, :unrealized_pnl
                )
            """, position)

    def insert_risk_decision(self, decision: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO risk_decisions VALUES (
                    :risk_decision_id, :request_id, :order_id, :allowed,
                    :severity, :reason, :checks_json, :timestamp_utc
                )
            """, decision)
