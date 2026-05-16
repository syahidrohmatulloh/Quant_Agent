
import pytest
import json
import tempfile
import os
from live_data.csv_replay_adapter import CSVReplayAdapter

def test_csv_replay_normalized():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([
            {"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002},
            {"symbol": "EURUSD", "bid": 1.1001, "ask": 1.1003}
        ], f)
        path = f.name
    try:
        adapter = CSVReplayAdapter(path)
        adapter.connect()
        tick1 = adapter.get_latest_tick("EURUSD")
        assert tick1["bid"] == 1.1000
        tick2 = adapter.get_latest_tick("EURUSD")
        assert tick2["bid"] == 1.1001
        adapter.disconnect()
    finally:
        os.unlink(path)

def test_csv_replay_csv_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("symbol,bid,ask,volume\n")
        f.write("EURUSD,1.1000,1.1002,100\n")
        f.write("EURUSD,1.1001,1.1003,200\n")
        path = f.name
    try:
        adapter = CSVReplayAdapter(path)
        adapter.connect()
        tick = adapter.get_latest_tick("EURUSD")
        assert tick["bid"] == 1.1000
        adapter.disconnect()
    finally:
        os.unlink(path)

def test_csv_replay_deterministic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}], f)
        path = f.name
    try:
        adapter = CSVReplayAdapter(path)
        adapter.connect()
        t1 = adapter.get_latest_tick("EURUSD")
        adapter.reset()
        t2 = adapter.get_latest_tick("EURUSD")
        # Compare everything except timestamp
        t1_copy = {k: v for k, v in t1.items() if k != "timestamp_utc"}
        t2_copy = {k: v for k, v in t2.items() if k != "timestamp_utc"}
        assert t1_copy == t2_copy
        adapter.disconnect()
    finally:
        os.unlink(path)

def test_csv_replay_finished():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}], f)
        path = f.name
    try:
        adapter = CSVReplayAdapter(path)
        adapter.connect()
        adapter.get_latest_tick("EURUSD")
        health = adapter.health_check()
        assert health["finished"] is True
        adapter.disconnect()
    finally:
        os.unlink(path)
