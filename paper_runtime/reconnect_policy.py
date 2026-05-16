"""Session reconnect policy with exponential backoff."""
from dataclasses import dataclass
from typing import Set


@dataclass
class ReconnectPolicy:
    max_attempts: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_errors: Set[str] = None

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = {
                "connection_reset", "timeout", "temporary_failure",
                "dependency_missing", "mt5_init_failed",
            }

    def is_retryable(self, error_reason: str) -> bool:
        return error_reason in self.retryable_errors

    def delay_for_attempt(self, attempt: int) -> float:
        import math
        delay = self.base_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)
