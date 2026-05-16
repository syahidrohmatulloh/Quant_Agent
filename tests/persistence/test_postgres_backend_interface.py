
import pytest
from persistence.postgres_backend import PostgresBackend

def test_postgres_backend_dry_run():
    backend = PostgresBackend(dsn="postgresql://user:pass@localhost/db")
    assert backend.is_available() is False  # psycopg not installed in test env

def test_postgres_backend_connect_fails_gracefully():
    backend = PostgresBackend()
    with pytest.raises(RuntimeError, match="psycopg not installed"):
        backend.connect()
