"""Tests for OANDA practice adapter."""
import pytest
from broker_integration.oanda.oanda_practice_adapter import OandaPracticeAdapter
from broker_integration.broker_config import BrokerConfig


def test_oanda_health_missing_credentials():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    adapter = OandaPracticeAdapter(config)
    h = adapter.health_check()
    assert h["healthy"] is False
    assert "missing_credentials" in h["reason"]


def test_oanda_health_with_key(monkeypatch):
    monkeypatch.setenv("OANDA_API_KEY", "test-key")
    config = BrokerConfig(broker_name="oanda", environment="practice", api_key_env="OANDA_API_KEY")
    adapter = OandaPracticeAdapter(config)
    h = adapter.health_check()
    assert h["healthy"] is True
    monkeypatch.delenv("OANDA_API_KEY")


def test_oanda_snapshot_masks_account(monkeypatch):
    monkeypatch.setenv("OANDA_API_KEY", "test-key")
    monkeypatch.setenv("OANDA_ACCOUNT_ID", "1234567890")
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        api_key_env="OANDA_API_KEY", account_id_env="OANDA_ACCOUNT_ID"
    )
    adapter = OandaPracticeAdapter(config)
    snap = adapter.get_account_snapshot()
    assert snap is not None
    assert "****7890" in snap["account_id_masked"]
    assert "1234567890" not in snap["account_id_masked"]


def test_oanda_normalize_tick():
    from broker_integration.oanda.oanda_market_data import normalize_oanda_tick
    raw = {"instrument": "EURUSD", "time": "2024-01-01T00:00:00Z", "bid": 1.1000, "ask": 1.1005}
    tick = normalize_oanda_tick("EURUSD", raw)
    assert tick["symbol"] == "EURUSD"
    assert tick["bid"] == 1.1000
    assert tick["ask"] == 1.1005
    assert tick["mid"] == 1.10025
    assert tick["spread"] == 0.0005
    assert tick["source"] == "oanda_practice"


def test_oanda_reconciliation():
    from broker_integration.oanda.oanda_reconciliation import reconcile_oanda
    internal = {"cash": 100000, "equity": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 1}]}
    broker = {"cash": 100000, "equity": 100000, "open_positions": [{"instrument": "EURUSD", "volume": 1}]}
    result = reconcile_oanda(internal, broker)
    assert result["status"] == "matched"
