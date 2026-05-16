"""Rate limiter for HTTP requests."""
import time
from dataclasses import dataclass


@dataclass
class RateLimiter:
    max_requests_per_second: float = 10.0
    min_interval_seconds: float = 0.0

    def __post_init__(self):
        if self.min_interval_seconds <= 0 and self.max_requests_per_second > 0:
            self.min_interval_seconds = 1.0 / self.max_requests_per_second
        self._last_request_time: float = 0.0

    def wait_if_needed(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)
        self._last_request_time = time.time()
