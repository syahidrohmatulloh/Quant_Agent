
import os
from typing import Any

class ConnectionManager:
    def __init__(self, backend: str = "sqlite", dsn: str = ""):
        self.backend = backend
        self.dsn = dsn or os.getenv("QUANT_SQLITE_PATH", "./data/quant_platform.db")
        self._conn = None

    def connect(self) -> Any:
        if self.backend == "sqlite":
            import sqlite3
            self._conn = sqlite3.connect(self.dsn, check_same_thread=False)
            return self._conn
        elif self.backend == "postgres":
            try:
                import psycopg
                self._conn = psycopg.connect(self.dsn)
                return self._conn
            except ImportError:
                raise RuntimeError("psycopg not installed. Install with: pip install psycopg")
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
