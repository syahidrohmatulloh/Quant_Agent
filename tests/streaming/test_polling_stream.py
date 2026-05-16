"""Tests for generic polling stream."""
from streaming.polling_stream import PollingStream
from streaming.stream_supervisor import StreamSupervisor


def test_polling_stream_emits_events():
    def fetch_fn(symbol):
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1005, "source": "test"}

    stream = PollingStream(fetch_fn, poll_interval_seconds=0.01, max_events=3)
    events = list(stream.start("EURUSD"))
    assert len(events) == 3
    assert events[0]["event_type"] == "tick"
    assert events[0]["payload"]["bid"] == 1.1


def test_polling_stream_with_supervisor():
    def fetch_fn(symbol):
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1005}

    supervisor = StreamSupervisor(stream_id="poll-001")
    stream = PollingStream(fetch_fn, poll_interval_seconds=0.01, max_events=2, supervisor=supervisor)
    supervisor.start()
    events = list(stream.start("EURUSD"))
    supervisor.stop()
    assert len(events) == 2
    assert supervisor.status()["health"]["events_received"] == 2


def test_polling_stream_stop():
    def fetch_fn(symbol):
        return {"symbol": symbol, "bid": 1.1, "ask": 1.1005}

    stream = PollingStream(fetch_fn, poll_interval_seconds=0.01, max_events=100)
    events = []
    for event in stream.start("EURUSD"):
        events.append(event)
        if len(events) >= 2:
            stream.stop()
    assert len(events) == 2
