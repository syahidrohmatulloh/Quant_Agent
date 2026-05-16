
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from persistence.connection import ConnectionManager

class Repository:
    def __init__(self, conn_manager: ConnectionManager):
        self.conn = conn_manager

    def _execute(self, sql: str, params: tuple = ()):
        c = self.conn.connect()
        try:
            c.execute(sql, params)
            c.commit()
        finally:
            self.conn.close()

    def _fetchall(self, sql: str, params: tuple = ()) -> List[Any]:
        c = self.conn.connect()
        try:
            cur = c.execute(sql, params)
            return cur.fetchall()
        finally:
            self.conn.close()

    def save_signal(self, signal: Dict[str, Any]):
        self._execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                model_id TEXT,
                model_version TEXT,
                signal TEXT,
                confidence REAL,
                generated INTEGER,
                reason TEXT,
                timestamp_utc TEXT,
                payload_json TEXT
            )
        """)
        self._execute("""
            INSERT OR REPLACE INTO signals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.get("signal_id", str(uuid.uuid4())),
            signal.get("model_id", ""),
            signal.get("model_version", ""),
            signal.get("signal", ""),
            signal.get("confidence", 0.0),
            1 if signal.get("generated") else 0,
            signal.get("reason", ""),
            signal.get("prediction_timestamp", datetime.now(timezone.utc).isoformat()),
            json.dumps(signal, default=str)
        ))

    def get_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        self._execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                model_id TEXT,
                model_version TEXT,
                signal TEXT,
                confidence REAL,
                generated INTEGER,
                reason TEXT,
                timestamp_utc TEXT,
                payload_json TEXT
            )
        """)
        rows = self._fetchall("SELECT payload_json FROM signals ORDER BY timestamp_utc DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in rows]

    def save_alert(self, alert: Dict[str, Any]):
        self._execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                level TEXT,
                category TEXT,
                message TEXT,
                details_json TEXT,
                created_at TEXT,
                acknowledged INTEGER,
                acknowledged_by TEXT,
                acknowledged_at TEXT
            )
        """)
        self._execute("""
            INSERT OR REPLACE INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.get("alert_id", str(uuid.uuid4())),
            alert.get("level", "info"),
            alert.get("category", ""),
            alert.get("message", ""),
            json.dumps(alert.get("details", {})),
            alert.get("created_at", datetime.now(timezone.utc).isoformat()),
            1 if alert.get("acknowledged") else 0,
            alert.get("acknowledged_by", ""),
            alert.get("acknowledged_at", "")
        ))

    def get_alerts(self, limit: int = 50, acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
        self._execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                level TEXT,
                category TEXT,
                message TEXT,
                details_json TEXT,
                created_at TEXT,
                acknowledged INTEGER,
                acknowledged_by TEXT,
                acknowledged_at TEXT
            )
        """)
        if acknowledged is not None:
            rows = self._fetchall("SELECT * FROM alerts WHERE acknowledged = ? ORDER BY created_at DESC LIMIT ?",
                                  (1 if acknowledged else 0, limit))
        else:
            rows = self._fetchall("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
        cols = ["alert_id", "level", "category", "message", "details_json", "created_at", "acknowledged", "acknowledged_by", "acknowledged_at"]
        return [dict(zip(cols, r)) for r in rows]

    def acknowledge_alert(self, alert_id: str, user: str):
        self._execute("""
            UPDATE alerts SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
            WHERE alert_id = ?
        """, (user, datetime.now(timezone.utc).isoformat(), alert_id))

    def save_heartbeat(self, heartbeat: Dict[str, Any]):
        self._execute("""
            CREATE TABLE IF NOT EXISTS heartbeats (
                component TEXT PRIMARY KEY,
                heartbeat_id TEXT,
                last_beat TEXT,
                status TEXT,
                metadata_json TEXT
            )
        """)
        self._execute("""
            INSERT OR REPLACE INTO heartbeats VALUES (?, ?, ?, ?, ?)
        """, (
            heartbeat.get("component", "unknown"),
            heartbeat.get("heartbeat_id", ""),
            heartbeat.get("last_beat", ""),
            heartbeat.get("status", ""),
            json.dumps(heartbeat.get("metadata", {}))
        ))

    def get_heartbeat(self, component: str) -> Optional[Dict[str, Any]]:
        self._execute("""
            CREATE TABLE IF NOT EXISTS heartbeats (
                component TEXT PRIMARY KEY,
                heartbeat_id TEXT,
                last_beat TEXT,
                status TEXT,
                metadata_json TEXT
            )
        """)
        rows = self._fetchall("SELECT * FROM heartbeats WHERE component = ?", (component,))
        if not rows:
            return None
        cols = ["component", "heartbeat_id", "last_beat", "status", "metadata_json"]
        return dict(zip(cols, rows[0]))
