"""Tests for broker reconciliation."""
from paper_runtime.broker_reconciliation import BrokerReconciliation


def test_matched_state():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "equity": 100000, "currency": "USD", "open_positions": [], "open_orders": []}
    broker = {"cash": 100000, "equity": 100000, "currency": "USD", "open_positions": [], "open_orders": []}
    result = rec.reconcile(internal, broker)
    assert result["status"] == "matched"


def test_quantity_mismatch():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 1, "entry_price": 1.1}]}
    broker = {"cash": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 2, "entry_price": 1.1}]}
    result = rec.reconcile(internal, broker)
    assert result["status"] == "mismatch"
    assert any(m["field"] == "quantity_mismatch" for m in result["mismatches"])


def test_missing_broker_position():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 1}]}
    broker = {"cash": 100000, "open_positions": []}
    result = rec.reconcile(internal, broker)
    assert any(m["field"] == "missing_broker_position" for m in result["mismatches"])


def test_extra_broker_position():
    rec = BrokerReconciliation()
    internal = {"cash": 100000, "open_positions": []}
    broker = {"cash": 100000, "open_positions": [{"symbol": "EURUSD", "volume": 1}]}
    result = rec.reconcile(internal, broker)
    assert any(m["field"] == "extra_broker_position" for m in result["mismatches"])


def test_stale_snapshot_warning():
    rec = BrokerReconciliation(max_age_seconds=1)
    from datetime import datetime, timezone
    old_ts = datetime.now(timezone.utc).isoformat()
    import time
    time.sleep(1.1)
    internal = {"cash": 100000}
    broker = {"cash": 100000, "timestamp_utc": old_ts}
    result = rec.reconcile(internal, broker)
    assert any(w["field"] == "stale_snapshot" for w in result["warnings"])


def test_no_secrets_in_output():
    rec = BrokerReconciliation()
    result = rec.reconcile({}, {})
    result_str = str(result)
    assert "api_key" not in result_str.lower()
    assert "secret" not in result_str.lower()
