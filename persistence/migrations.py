
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from persistence.connection import ConnectionManager

MIGRATIONS: List[Dict[str, Any]] = [
    {
        "version": 1,
        "description": "Create migration_versions table",
        "sql": "CREATE TABLE IF NOT EXISTS migration_versions (version INTEGER PRIMARY KEY, applied_at TEXT)"
    },
    {
        "version": 2,
        "description": "Create signals table",
        "sql": """
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
        """
    },
    {
        "version": 3,
        "description": "Create alerts table",
        "sql": """
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
        """
    },
    {
        "version": 4,
        "description": "Create heartbeats table",
        "sql": """
            CREATE TABLE IF NOT EXISTS heartbeats (
                component TEXT PRIMARY KEY,
                heartbeat_id TEXT,
                last_beat TEXT,
                status TEXT,
                metadata_json TEXT
            )
        """
    }
]

class MigrationRunner:
    def __init__(self, conn_manager: ConnectionManager):
        self.conn = conn_manager

    def _ensure_versions_table(self):
        c = self.conn.connect()
        try:
            c.execute("CREATE TABLE IF NOT EXISTS migration_versions (version INTEGER PRIMARY KEY, applied_at TEXT)")
            c.commit()
        finally:
            self.conn.close()

    def get_applied_versions(self) -> List[int]:
        self._ensure_versions_table()
        c = self.conn.connect()
        try:
            cur = c.execute("SELECT version FROM migration_versions ORDER BY version")
            return [r[0] for r in cur.fetchall()]
        finally:
            self.conn.close()

    def apply_all(self):
        applied = set(self.get_applied_versions())
        for mig in MIGRATIONS:
            if mig["version"] not in applied:
                self._apply_single(mig)

    def _apply_single(self, mig: Dict[str, Any]):
        c = self.conn.connect()
        try:
            c.execute(mig["sql"])
            c.execute("INSERT OR REPLACE INTO migration_versions (version, applied_at) VALUES (?, ?)",
                      (mig["version"], datetime.now(timezone.utc).isoformat()))
            c.commit()
        finally:
            self.conn.close()

    def is_up_to_date(self) -> bool:
        applied = self.get_applied_versions()
        versions = [m["version"] for m in MIGRATIONS]
        return applied == versions
