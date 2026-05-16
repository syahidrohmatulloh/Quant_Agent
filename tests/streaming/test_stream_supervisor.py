"""Tests for stream supervisor."""
import time
from streaming.stream_supervisor import StreamSupervisor


def test_supervisor_start_stop():
    s = StreamSupervisor(stream_id="test-001")
    s.start()
    assert s.is_running() is True
    s.stop()
    assert s.is_running() is False


def test_supervisor_records_events():
    s = StreamSupervisor(stream_id="test-002")
    s.start()
    s.record_event()
    s.record_event()
    status = s.status()
    assert status["health"]["events_received"] == 2
    s.stop()


def test_supervisor_stops_on_max_errors():
    s = StreamSupervisor(stream_id="test-003", max_errors=3)
    s.start()
    s.record_error("e1")
    s.record_error("e2")
    assert s.is_running() is True
    s.record_error("e3")
    assert s.is_running() is False


def test_supervisor_stops_on_max_reconnects():
    s = StreamSupervisor(stream_id="test-004", max_errors=100)
    s.start()
    for _ in range(5):
        s.record_reconnect()
    assert s.is_running() is False
