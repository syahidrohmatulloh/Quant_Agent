
import pytest
from scheduler.retry_policy import RetryPolicy

def test_retry_succeeds_eventually():
    calls = [0]
    def flaky():
        calls[0] += 1
        if calls[0] < 3:
            raise RuntimeError("fail")
        return "ok"
    policy = RetryPolicy(max_attempts=5, backoff_seconds=0.01)
    result = policy.execute(flaky)
    assert result == "ok"
    assert calls[0] == 3

def test_retry_exhausts():
    def always_fail():
        raise RuntimeError("fail")
    policy = RetryPolicy(max_attempts=2, backoff_seconds=0.01)
    with pytest.raises(RuntimeError, match="fail"):
        policy.execute(always_fail)

def test_should_retry_exception():
    policy = RetryPolicy(retryable_exceptions=(ValueError,))
    assert policy.should_retry(ValueError("x")) is True
    assert policy.should_retry(RuntimeError("x")) is False
