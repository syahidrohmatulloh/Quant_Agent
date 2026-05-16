"""Tests for broker health utilities."""
from broker_integration.broker_health import healthy, unhealthy


def test_healthy():
    h = healthy("ok", "ready")
    assert h["healthy"] is True
    assert h["status"] == "ok"


def test_unhealthy():
    h = unhealthy("missing_credentials")
    assert h["healthy"] is False
    assert h["reason"] == "missing_credentials"
