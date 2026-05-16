"""Stream reconnect policy."""
from dataclasses import dataclass
from typing import Set


@dataclass
class StreamReconnectPolicy:
    max_reconnect_attempts: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    retryable_errors: Set[str] = None

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = {
                "connection_reset", "timeout", "rate_limited",
                "dependency_missing", "transport_error",
            }

    def is_retryable(self, error_reason: str) -> bool:
        return error_reason in self.retryable_errors

    def delay_for_attempt(self, attempt: int) -> float:
        import math
        delay = self.base_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)
