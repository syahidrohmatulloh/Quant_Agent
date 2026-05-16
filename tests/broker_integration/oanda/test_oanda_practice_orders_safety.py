"""Tests for OANDA practice order safety."""
import pytest
from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_practice_orders import OandaPracticeOrderClient
from broker_integration.transport.network_errors import LiveTradingDisabledError


def test_order_default_disabled():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    client = OandaPracticeOrderClient(config)
    result = client.submit_order("EURUSD", "buy", 1000)
    assert result["executed"] is False
    assert result["reason"] == "order_submission_disabled"
    assert result["paper_only"] is True


def test_order_dry_run():
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        allow_order_submission=True,
    )
    client = OandaPracticeOrderClient(config)
    result = client.submit_order("EURUSD", "buy", 1000, dry_run=True)
    assert result["executed"] is False
    assert result["reason"] == "dry_run"
    assert result["paper_only"] is True
    assert "audit" in result
    assert "payload" in result


def test_order_live_orders_rejected():
    with pytest.raises(BrokerConfigError):
        config = BrokerConfig(
            broker_name="oanda", environment="practice",
            allow_order_submission=True,
            allow_live_orders=True,
        )


def test_order_live_env_rejected():
    with pytest.raises(BrokerConfigError):
        config = BrokerConfig(
            broker_name="oanda", environment="live",
            allow_order_submission=True,
        )


def test_order_audit_fields():
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        allow_order_submission=True,
    )
    client = OandaPracticeOrderClient(config)
    result = client.submit_order(
        "EURUSD", "buy", 1000,
        dry_run=True,
        model_id="model-001",
        signal_id="signal-001",
    )
    assert result["audit"]["model_id"] == "model-001"
    assert result["audit"]["signal_id"] == "signal-001"


def test_order_symbol_conversion():
    config = BrokerConfig(
        broker_name="oanda", environment="practice",
        allow_order_submission=True,
    )
    client = OandaPracticeOrderClient(config)
    result = client.submit_order("EURUSD", "buy", 1000, dry_run=True)
    assert result["payload"]["order"]["instrument"] == "EUR_USD"
