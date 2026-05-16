
import sqlite3
from typing import Any
from persistence.connection import ConnectionManager

class SQLiteBackend:
    def __init__(self, dsn: str = "./data/quant_platform.db"):
        self.conn = ConnectionManager(backend="sqlite", dsn=dsn)

    def init_tables(self):
        c = self.conn.connect()
        try:
            c.execute("CREATE TABLE IF NOT EXISTS migration_versions (version INTEGER PRIMARY KEY, applied_at TEXT)")
            c.commit()
        finally:
            self.conn.close()
