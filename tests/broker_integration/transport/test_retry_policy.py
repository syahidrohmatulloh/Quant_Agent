"""Tests for retry policy."""
from broker_integration.transport.retry_policy import RetryPolicy


def test_retryable_status_codes():
    p = RetryPolicy()
    assert p.is_retryable_status(429) is True
    assert p.is_retryable_status(500) is True
    assert p.is_retryable_status(400) is False


def test_delay_calculation():
    p = RetryPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0, max_delay_seconds=10.0, jitter=False)
    assert p.delay_for_attempt(0) == 1.0
    assert p.delay_for_attempt(1) == 2.0
    assert p.delay_for_attempt(2) == 4.0
    assert p.delay_for_attempt(10) == 10.0  # capped


def test_retryable_exception():
    p = RetryPolicy()
    assert p.is_retryable_exception(ValueError()) is False
