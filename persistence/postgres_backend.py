
from typing import Any, Optional
from persistence.connection import ConnectionManager

class PostgresBackend:
    def __init__(self, dsn: str = ""):
        self.dsn = dsn
        self._available = False
        self._try_connect()

    def _try_connect(self):
        try:
            import psycopg
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def connect(self) -> Any:
        if not self._available:
            raise RuntimeError("psycopg not installed")
        conn = ConnectionManager(backend="postgres", dsn=self.dsn)
        return conn.connect()

    def init_tables(self):
        c = self.connect()
        try:
            c.execute("CREATE TABLE IF NOT EXISTS migration_versions (version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW())")
            c.commit()
        finally:
            c.close()
