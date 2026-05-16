"""Tests for stream reconnect policy."""
from streaming.stream_reconnect import StreamReconnectPolicy


def test_reconnect_retryable():
    p = StreamReconnectPolicy()
    assert p.is_retryable("timeout") is True
    assert p.is_retryable("fatal") is False


def test_reconnect_delay():
    p = StreamReconnectPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0, max_delay_seconds=10.0)
    assert p.delay_for_attempt(0) == 1.0
    assert p.delay_for_attempt(1) == 2.0
    assert p.delay_for_attempt(2) == 4.0
    assert p.delay_for_attempt(10) == 10.0
