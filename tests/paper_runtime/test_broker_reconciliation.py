"""Tests for broker reconciliation."""
from paper_runtime.broker_reconciliation import BrokerReconciliation


def test_reconciliation_matched():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "equity": 100000, "currency": "USD", "open_positions": [], "open_orders": []}
    broker = {"cash": 100000, "equity": 100000, "currency": "USD", "open_positions": [], "open_orders": []}
    result = rec.reconcile(internal, broker)
    assert result["status"] == "matched"


def test_reconciliation_severe_detection():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 1}]}
    broker = {"cash": 100000, "open_positions": []}
    result = rec.reconcile(internal, broker)
    assert rec.is_severe(result) is True
