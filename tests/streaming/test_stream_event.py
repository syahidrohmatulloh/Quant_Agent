"""Tests for stream events."""
from streaming.stream_event import StreamEvent, tick_event, heartbeat_event, error_event


def test_stream_event_defaults():
    e = StreamEvent()
    assert e.event_type == "tick"
    assert e.event_id != ""
    assert e.timestamp_utc != ""


def test_tick_event():
    e = tick_event("EURUSD", 1.1000, 1.1005)
    assert e.symbol == "EURUSD"
    assert e.payload["bid"] == 1.1000
    assert e.payload["mid"] == 1.10025
    assert e.payload["spread"] == 0.0005


def test_heartbeat_event():
    e = heartbeat_event()
    assert e.event_type == "heartbeat"


def test_error_event():
    e = error_event("timeout")
    assert e.event_type == "error"
    assert e.payload["error"] == "timeout"
