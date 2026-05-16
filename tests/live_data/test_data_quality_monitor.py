
import pytest
from datetime import datetime, timezone
from live_data.data_quality_monitor import DataQualityMonitor

def test_fresh_tick_passes():
    monitor = DataQualityMonitor(max_stale_seconds=30)
    tick = {
        "symbol": "EURUSD",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "bid": 1.1000, "ask": 1.1002, "spread": 0.0002
    }
    issues = monitor.check_tick(tick)
    assert len(issues) == 0
    assert monitor.is_healthy(tick) is True

def test_stale_tick_detected():
    monitor = DataQualityMonitor(max_stale_seconds=1)
    old = datetime.now(timezone.utc).isoformat()
    tick = {"symbol": "EURUSD", "timestamp_utc": old, "bid": 1.1, "ask": 1.1002, "spread": 0.0002}
    import time
    time.sleep(1.1)
    issues = monitor.check_tick(tick)
    assert any(i["type"] == "stale" for i in issues)

def test_missing_bid_ask_detected():
    monitor = DataQualityMonitor()
    tick = {"symbol": "EURUSD", "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    issues = monitor.check_tick(tick)
    assert any(i["type"] == "missing_bid_ask" for i in issues)

def test_invalid_price_detected():
    monitor = DataQualityMonitor()
    tick = {"symbol": "EURUSD", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "bid": 0, "ask": 1.1}
    issues = monitor.check_tick(tick)
    assert any(i["type"] == "invalid_price" for i in issues)

def test_wide_spread_detected():
    monitor = DataQualityMonitor(max_spread_multiplier=2.0)
    tick1 = {"symbol": "EURUSD", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "bid": 1.1, "ask": 1.1002, "spread": 0.0002}
    monitor.check_tick(tick1)
    tick2 = {"symbol": "EURUSD", "timestamp_utc": datetime.now(timezone.utc).isoformat(), "bid": 1.1, "ask": 1.1010, "spread": 0.0010}
    issues = monitor.check_tick(tick2)
    assert any(i["type"] == "wide_spread" for i in issues)

def test_backwards_timestamp_detected():
    monitor = DataQualityMonitor()
    now = datetime.now(timezone.utc)
    tick1 = {"symbol": "EURUSD", "timestamp_utc": now.isoformat(), "bid": 1.1, "ask": 1.1002}
    monitor.check_tick(tick1)
    earlier = now.replace(minute=now.minute - 1)
    tick2 = {"symbol": "EURUSD", "timestamp_utc": earlier.isoformat(), "bid": 1.1, "ask": 1.1002}
    issues = monitor.check_tick(tick2)
    assert any(i["type"] == "backwards_timestamp" for i in issues)

def test_duplicate_bars_detected():
    monitor = DataQualityMonitor()
    bars = [
        {"symbol": "EURUSD", "timestamp_utc": "2024-01-01T00:00:00"},
        {"symbol": "EURUSD", "timestamp_utc": "2024-01-01T00:00:00"}
    ]
    issues = monitor.check_bars("EURUSD", bars)
    assert any(i["type"] == "duplicate_bars" for i in issues)
