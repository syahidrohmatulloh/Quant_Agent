"""Tests for stream health."""
import time
from streaming.stream_health import StreamHealth


def test_stream_health_initial():
    h = StreamHealth()
    result = h.check()
    assert result["healthy"] is True  # no events yet, not stale
    assert result["events_received"] == 0


def test_stream_health_records_event():
    h = StreamHealth(stale_after_seconds=1.0)
    h.record_event()
    result = h.check()
    assert result["events_received"] == 1
    assert result["stale"] is False


def test_stream_health_stale():
    h = StreamHealth(stale_after_seconds=0.1)
    h.record_event()
    time.sleep(0.15)
    result = h.check()
    assert result["stale"] is True
    assert result["healthy"] is False


def test_stream_health_too_many_errors():
    h = StreamHealth()
    for _ in range(10):
        h.record_error()
    result = h.check()
    assert result["healthy"] is False
    assert result["errors"] == 10
