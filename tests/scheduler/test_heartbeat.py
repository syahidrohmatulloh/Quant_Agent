
import pytest
import time
from scheduler.heartbeat import Heartbeat

def test_heartbeat_records():
    hb = Heartbeat(component="test")
    hb.beat("ok", {"jobs": 5})
    assert hb.status == "ok"
    assert hb.metadata["jobs"] == 5
    assert hb.last_beat is not None

def test_heartbeat_not_stale_immediately():
    hb = Heartbeat()
    hb.beat()
    assert hb.is_stale(max_age_seconds=60) is False

def test_heartbeat_stale_after_delay():
    hb = Heartbeat()
    hb.beat()
    time.sleep(1.1)
    assert hb.is_stale(max_age_seconds=1) is True

def test_heartbeat_dict():
    hb = Heartbeat(component="x")
    hb.beat("running")
    d = hb.to_dict()
    assert d["component"] == "x"
    assert d["status"] == "running"
