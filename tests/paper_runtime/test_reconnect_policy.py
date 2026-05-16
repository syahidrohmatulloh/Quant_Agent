"""Tests for reconnect policy."""
from paper_runtime.reconnect_policy import ReconnectPolicy


def test_default_retryable_errors():
    p = ReconnectPolicy()
    assert p.is_retryable("connection_reset") is True
    assert p.is_retryable("timeout") is True
    assert p.is_retryable("dependency_missing") is True
    assert p.is_retryable("invalid_password") is False


def test_backoff_calculation():
    p = ReconnectPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0, max_delay_seconds=10.0)
    assert p.delay_for_attempt(0) == 1.0
    assert p.delay_for_attempt(1) == 2.0
    assert p.delay_for_attempt(2) == 4.0
    assert p.delay_for_attempt(10) == 10.0  # capped at max_delay
