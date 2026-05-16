"""Tests for auth utilities."""
import os
import pytest
from broker_integration.transport.auth import EnvAuth


def test_auth_reads_from_env(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "my-key")
    auth = EnvAuth(api_key_env="TEST_API_KEY")
    assert auth.api_key == "my-key"
    assert auth.is_configured() is True
    headers = auth.build_headers()
    assert headers["Authorization"] == "Bearer my-key"
    monkeypatch.delenv("TEST_API_KEY")


def test_auth_missing_key():
    auth = EnvAuth(api_key_env="MISSING_KEY")
    assert auth.api_key is None
    assert auth.is_configured() is False


def test_auth_repr_no_secret():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("TEST_KEY", "secret123")
    auth = EnvAuth(api_key_env="TEST_KEY")
    r = repr(auth)
    assert "secret123" not in r
    assert "set" in r
    monkeypatch.undo()
