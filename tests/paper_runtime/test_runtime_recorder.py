"""Tests for runtime recorder."""
import os
import json
from paper_runtime.runtime_recorder import RuntimeRecorder


def test_recorder_creates_output_dir():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-001")
    assert os.path.exists(rec.output_dir)


def test_recorder_writes_ticks():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-002")
    rec.record_tick({"symbol": "EURUSD", "bid": 1.1, "ask": 1.1005, "timestamp_utc": "2024-01-01T00:00:00Z"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "ticks.csv"))


def test_recorder_writes_signals():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-003")
    rec.record_signal({"symbol": "EURUSD", "direction": "buy"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "signals.csv"))


def test_recorder_writes_rejections():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-004")
    rec.record_rejection({"reason": "wide_spread"})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "rejections.csv"))


def test_recorder_writes_snapshots():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-005")
    rec.record_snapshot({"cash": 100000})
    rec.flush()
    assert os.path.exists(os.path.join(rec.output_dir, "snapshots.json"))


def test_recorder_writes_summary():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-006")
    rec.flush()
    path = os.path.join(rec.output_dir, "session_summary.json")
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert data["ticks_count"] == 0


def test_no_secrets_in_outputs():
    rec = RuntimeRecorder("/tmp/test_recorder", "rec-007")
    rec.record_tick({"symbol": "EURUSD", "api_key": "secret123", "bid": 1.1})
    rec.flush()
    path = os.path.join(rec.output_dir, "ticks.csv")
    with open(path) as f:
        content = f.read()
    assert "secret123" not in content
    assert "***REDACTED***" in content
