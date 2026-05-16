
import pytest
import os
import tempfile
from persistence.connection import ConnectionManager
from persistence.repository import Repository

def test_save_and_get_signals():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        repo = Repository(conn)
        repo.save_signal({"signal_id": "s1", "model_id": "m1", "model_version": "v1", "signal": "buy", "confidence": 0.7, "generated": True})
        signals = repo.get_signals(limit=10)
        assert len(signals) == 1
        assert signals[0]["signal_id"] == "s1"

def test_save_and_get_alerts():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        repo = Repository(conn)
        repo.save_alert({"alert_id": "a1", "level": "critical", "category": "drawdown", "message": "DD > 10%"})
        alerts = repo.get_alerts(limit=10)
        assert len(alerts) == 1
        assert alerts[0]["alert_id"] == "a1"

def test_acknowledge_alert():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        repo = Repository(conn)
        repo.save_alert({"alert_id": "a1", "level": "high", "category": "test", "message": "x"})
        repo.acknowledge_alert("a1", "admin")
        alerts = repo.get_alerts(acknowledged=True)
        assert len(alerts) == 1
        assert alerts[0]["acknowledged_by"] == "admin"

def test_save_and_get_heartbeat():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = os.path.join(tmpdir, "test.db")
        conn = ConnectionManager(backend="sqlite", dsn=db)
        repo = Repository(conn)
        repo.save_heartbeat({"component": "scheduler", "heartbeat_id": "h1", "last_beat": "2024-01-01T00:00:00", "status": "ok", "metadata": {}})
        hb = repo.get_heartbeat("scheduler")
        assert hb is not None
        assert hb["status"] == "ok"
