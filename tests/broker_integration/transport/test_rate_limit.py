"""Tests for rate limiter."""
import time
from broker_integration.transport.rate_limit import RateLimiter


def test_rate_limiter_interval():
    rl = RateLimiter(max_requests_per_second=10.0)
    assert rl.min_interval_seconds == 0.1


def test_rate_limiter_wait():
    rl = RateLimiter(max_requests_per_second=1000.0)
    start = time.time()
    rl.wait_if_needed()
    elapsed = time.time() - start
    assert elapsed < 0.01  # very fast at 1000 rps
