
import time
from typing import Callable, Any, Optional, Type, Tuple

class RetryPolicy:
    def __init__(self, max_attempts: int = 3, backoff_seconds: float = 1.0,
                 retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None):
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        last_error = None
        for attempt in range(self.max_attempts):
            try:
                return fn(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_error = e
                if attempt < self.max_attempts - 1:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
        raise last_error

    def should_retry(self, exception: Exception) -> bool:
        return isinstance(exception, self.retryable_exceptions)
