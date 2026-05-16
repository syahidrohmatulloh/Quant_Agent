"""Tests for Alpaca paper adapter."""
import pytest
from broker_integration.alpaca.alpaca_paper_adapter import AlpacaPaperAdapter
from broker_integration.broker_config import BrokerConfig


def test_alpaca_health_missing_credentials():
    config = BrokerConfig(broker_name="alpaca", environment="paper")
    adapter = AlpacaPaperAdapter(config)
    h = adapter.health_check()
    assert h["healthy"] is False
    assert "missing_credentials" in h["reason"]


def test_alpaca_health_with_key(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    config = BrokerConfig(broker_name="alpaca", environment="paper", api_key_env="ALPACA_API_KEY")
    adapter = AlpacaPaperAdapter(config)
    h = adapter.health_check()
    assert h["healthy"] is True
    monkeypatch.delenv("ALPACA_API_KEY")


def test_alpaca_normalize_tick():
    from broker_integration.alpaca.alpaca_market_data import normalize_alpaca_tick
    raw = {"bid_price": 150.0, "ask_price": 150.01, "volume": 1000}
    tick = normalize_alpaca_tick("AAPL", raw)
    assert tick["symbol"] == "AAPL"
    assert tick["mid"] == 150.005
    assert tick["source"] == "alpaca_paper"
