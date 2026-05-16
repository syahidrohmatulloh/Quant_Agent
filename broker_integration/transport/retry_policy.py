"""Retry policy with exponential backoff."""
import time
import random
from dataclasses import dataclass
from typing import Set, Optional, Type


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: Set[int] = None
    retryable_exceptions: Set[Type[Exception]] = None
    jitter: bool = True

    def __post_init__(self):
        if self.retryable_status_codes is None:
            self.retryable_status_codes = {429, 500, 502, 503, 504}
        if self.retryable_exceptions is None:
            self.retryable_exceptions = set()

    def is_retryable_status(self, status_code: int) -> bool:
        return status_code in self.retryable_status_codes

    def is_retryable_exception(self, exc: Exception) -> bool:
        return any(isinstance(exc, e) for e in self.retryable_exceptions)

    def delay_for_attempt(self, attempt: int) -> float:
        delay = self.base_delay_seconds * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay

    def sleep(self, attempt: int) -> None:
        time.sleep(self.delay_for_attempt(attempt))
