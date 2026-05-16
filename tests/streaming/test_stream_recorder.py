"""Tests for stream recorder."""
import os
import json
from streaming.stream_recorder import StreamRecorder


def test_recorder_creates_dir():
    rec = StreamRecorder("/tmp/test_stream", "rec-001")
    assert os.path.exists(rec.output_dir)


def test_recorder_writes_ticks():
    rec = StreamRecorder("/tmp/test_stream", "rec-002")
    rec.record_tick({"symbol": "EURUSD", "bid": 1.1, "ask": 1.1005, "timestamp_utc": "2024-01-01T00:00:00Z"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "ticks.csv"))


def test_recorder_writes_jsonl():
    rec = StreamRecorder("/tmp/test_stream", "rec-003")
    rec.record_event({"type": "tick"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "events.jsonl"))


def test_recorder_writes_errors():
    rec = StreamRecorder("/tmp/test_stream", "rec-004")
    rec.record_error({"msg": "timeout"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "errors.jsonl"))


def test_recorder_writes_summary():
    rec = StreamRecorder("/tmp/test_stream", "rec-005")
    rec.flush()
    path = os.path.join(rec.output_dir, "summary.json")
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert data["ticks_count"] == 0


def test_recorder_no_secrets():
    rec = StreamRecorder("/tmp/test_stream", "rec-006")
    rec.record_tick({"symbol": "EURUSD", "api_key": "secret123", "bid": 1.1})
    rec.flush()
    path = os.path.join(rec.output_dir, "ticks.csv")
    with open(path) as f:
        content = f.read()
    assert "secret123" not in content
    assert "***REDACTED***" in content
