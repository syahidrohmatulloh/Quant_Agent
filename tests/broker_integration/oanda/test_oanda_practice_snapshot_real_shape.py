"""Tests for OANDA practice snapshot with real shape."""
import pytest
from broker_integration.broker_config import BrokerConfig
from broker_integration.oanda.oanda_practice_snapshot import OandaPracticeSnapshot
from broker_integration.transport.mock_transport import MockTransport


def test_snapshot_missing_credentials():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    snapshot = OandaPracticeSnapshot(config)
    result = snapshot.fetch()
    assert result is None


def test_snapshot_missing_account():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("OANDA_API_KEY", "test-key")
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        api_key_env="OANDA_API_KEY",
    )
    snapshot = OandaPracticeSnapshot(config)
    result = snapshot.fetch()
    assert result is None
    monkeypatch.undo()


def test_snapshot_parse_shape():
    account = {
        "id": "001-001-1234567-001",
        "currency": "USD",
        "balance": "100000.00",
        "NAV": "100250.00",
        "marginUsed": "0.00",
    }
    positions_raw = {"positions": []}
    orders_raw = {"orders": []}

    from broker_integration.oanda.oanda_practice_snapshot import OandaPracticeSnapshot
    from broker_integration.broker_config import BrokerConfig
    config = BrokerConfig(broker_name="oanda", environment="practice")
    snapshot = OandaPracticeSnapshot(config)
    result = snapshot._build_snapshot(account, positions_raw, orders_raw)

    assert result["broker"] == "oanda"
    assert result["environment"] == "practice"
    assert "****0001" in result["account_id_masked"] or "****" in result["account_id_masked"]
    assert "001-001-1234567-001" not in result["account_id_masked"]
    assert result["currency"] == "USD"
    assert result["cash"] == 100000.0
    assert result["equity"] == 100250.0
    assert result["open_positions"] == []
    assert result["open_orders"] == []


def test_snapshot_no_secrets():
    account = {"id": "123", "currency": "USD", "balance": "0", "NAV": "0", "marginUsed": "0"}
    from broker_integration.oanda.oanda_practice_snapshot import OandaPracticeSnapshot
    from broker_integration.broker_config import BrokerConfig
    config = BrokerConfig(broker_name="oanda", environment="practice")
    snapshot = OandaPracticeSnapshot(config)
    result = snapshot._build_snapshot(account, {"positions": []}, {"orders": []})
    result_str = str(result)
    assert "api_key" not in result_str.lower()
    assert "secret" not in result_str.lower()
