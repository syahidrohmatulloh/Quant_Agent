
import pytest
import os
import tempfile
from persistence.connection import ConnectionManager
from persistence.migrations import MigrationRunner

def test_migrations_are_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        runner = MigrationRunner(conn)
        runner.apply_all()
        runner.apply_all()  # second time should not fail
        assert runner.is_up_to_date() is True

def test_migrations_create_expected_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        runner = MigrationRunner(conn)
        runner.apply_all()
        import sqlite3
        with sqlite3.connect(db) as c:
            cur = c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {r[0] for r in cur.fetchall()}
        assert "migration_versions" in tables
        assert "signals" in tables
        assert "alerts" in tables
        assert "heartbeats" in tables

def test_migration_versions_incremental():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        runner = MigrationRunner(conn)
        runner.apply_all()
        versions = runner.get_applied_versions()
        assert versions == [1, 2, 3, 4]
