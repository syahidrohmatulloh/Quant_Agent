"""Tests for broker integration base."""
import pytest
from broker_integration.base import BaseBrokerAdapter
from broker_integration.broker_config import BrokerConfig, BrokerConfigError


class MockAdapter(BaseBrokerAdapter):
    @property
    def broker_name(self):
        return "mock"

    @property
    def environment(self):
        return "paper"

    def health_check(self):
        return {"healthy": True}

    def get_account_snapshot(self):
        return {}

    def get_latest_tick(self, symbol):
        return {}

    def get_recent_bars(self, symbol, timeframe, lookback):
        return []

    def submit_paper_order(self, symbol, direction, volume, price):
        return {"executed": True}


def test_mock_adapter_basics():
    config = BrokerConfig(broker_name="mock", environment="paper")
    adapter = MockAdapter(config)
    assert adapter.broker_name == "mock"
    assert adapter.environment == "paper"
    assert adapter.live_trading_enabled is False
    assert adapter.supports_live_orders is False
    assert adapter.supports_market_data is True
