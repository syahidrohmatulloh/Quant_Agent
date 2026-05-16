"""Tests for IBKR paper adapter."""
import pytest
from broker_integration.ibkr.ibkr_paper_adapter import IbkrPaperAdapter
from broker_integration.broker_config import BrokerConfig


def test_ibkr_health_missing_credentials():
    config = BrokerConfig(broker_name="ibkr", environment="paper")
    adapter = IbkrPaperAdapter(config)
    h = adapter.health_check()
    assert h["healthy"] is False
    assert "missing_credentials" in h["reason"]


def test_ibkr_normalize_tick():
    from broker_integration.ibkr.ibkr_market_data import normalize_ibkr_tick
    raw = {"bid": 150.0, "ask": 150.01, "volume": 100}
    tick = normalize_ibkr_tick("AAPL", raw)
    assert tick["symbol"] == "AAPL"
    assert tick["mid"] == 150.005
    assert tick["source"] == "ibkr_paper"
