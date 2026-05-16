
import pytest
from datetime import datetime, timezone
from live_data.market_clock import MarketClock

def test_weekday_trading_open():
    clock = MarketClock()
    # Monday 12:00 UTC
    dt = datetime(2024, 1, 8, 12, 0, tzinfo=timezone.utc)
    assert clock.is_weekend(dt) is False
    assert clock.is_trading_window(dt) is True

def test_saturday_is_weekend():
    clock = MarketClock()
    dt = datetime(2024, 1, 6, 12, 0, tzinfo=timezone.utc)
    assert clock.is_weekend(dt) is True

def test_sunday_before_22_is_weekend():
    clock = MarketClock()
    dt = datetime(2024, 1, 7, 21, 0, tzinfo=timezone.utc)
    assert clock.is_weekend(dt) is True

def test_sunday_after_22_is_open():
    clock = MarketClock()
    dt = datetime(2024, 1, 7, 22, 30, tzinfo=timezone.utc)
    assert clock.is_weekend(dt) is False
    assert clock.is_trading_window(dt) is True

def test_friday_after_22_is_weekend():
    clock = MarketClock()
    dt = datetime(2024, 1, 5, 22, 30, tzinfo=timezone.utc)
    assert clock.is_weekend(dt) is True

def test_session_status_fields():
    clock = MarketClock()
    status = clock.session_status()
    assert "timestamp_utc" in status
    assert "is_weekend" in status
    assert "is_trading" in status
    assert "next_open" in status
