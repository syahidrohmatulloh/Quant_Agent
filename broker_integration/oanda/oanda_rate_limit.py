"""OANDA rate limiter."""
from broker_integration.transport.rate_limit import RateLimiter


class OandaRateLimiter(RateLimiter):
    """OANDA-specific rate limiter.

    OANDA practice: 100 requests/second max.
    Use conservative 20/second for safety.
    """
    def __init__(self, max_requests_per_second: float = 20.0):
        super().__init__(max_requests_per_second=max_requests_per_second)
