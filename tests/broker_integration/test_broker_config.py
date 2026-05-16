"""Tests for broker config safety gates."""
import os
import pytest
from broker_integration.broker_config import BrokerConfig, BrokerConfigError


def test_valid_paper_config():
    config = BrokerConfig(broker_name="oanda", environment="practice")
    assert config.paper_only is True
    assert config.allow_live_orders is False


def test_live_environment_rejected():
    with pytest.raises(BrokerConfigError):
        BrokerConfig(broker_name="oanda", environment="live")


def test_allow_live_orders_rejected():
    with pytest.raises(BrokerConfigError):
        BrokerConfig(broker_name="oanda", environment="paper", allow_live_orders=True)


def test_live_env_var_rejected(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    with pytest.raises(BrokerConfigError):
        BrokerConfig(broker_name="oanda", environment="paper")
    monkeypatch.delenv("LIVE_TRADING_ENABLED")


def test_missing_credentials_unhealthy():
    config = BrokerConfig(broker_name="oanda", environment="practice", api_key_env="MISSING_KEY")
    assert config.api_key is None


def test_no_secrets_in_repr():
    config = BrokerConfig(broker_name="oanda", environment="practice", api_key_env="KEY")
    r = repr(config)
    assert "api_key" not in r
    assert "secret" not in r
