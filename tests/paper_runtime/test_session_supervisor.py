"""Tests for session supervisor."""
import time
from paper_runtime.session_supervisor import SessionSupervisor
from paper_runtime.reconnect_policy import ReconnectPolicy
from paper_runtime.runtime_recorder import RuntimeRecorder


def test_supervisor_start_stop():
    sup = SessionSupervisor(session_id="sup-001")
    sup.start()
    assert sup.is_running() is True
    assert sup.state.status == "running"
    sup.stop()
    assert sup.is_running() is False
    assert sup.state.status == "stopped"


def test_retries_recoverable_errors():
    policy = ReconnectPolicy(max_attempts=3)
    assert policy.is_retryable("connection_reset") is True
    assert policy.is_retryable("fatal_error") is False
    assert policy.delay_for_attempt(0) == 1.0
    assert policy.delay_for_attempt(1) == 2.0


def test_stops_after_max_failures():
    sup = SessionSupervisor(session_id="sup-002", max_failures=3)
    sup.start()
    sup.record_cycle(False, "error1")
    sup.record_cycle(False, "error2")
    assert sup.is_running() is True
    sup.record_cycle(False, "error3")
    assert sup.is_running() is False
    assert sup.state.status == "error"


def test_heartbeat_updated():
    sup = SessionSupervisor(session_id="sup-003")
    sup.start()
    time.sleep(0.1)
    sup.update_heartbeat()
    assert "timestamp_utc" in sup.state.heartbeat
    assert sup.state.heartbeat["status"] == "running"
    sup.stop()


def test_state_persisted():
    recorder = RuntimeRecorder("/tmp/test_reports", "sup-004")
    sup = SessionSupervisor(session_id="sup-004", recorder=recorder)
    sup.start()
    sup.record_cycle(True)
    sup.stop()
    state = sup.export_state()
    assert state["session_id"] == "sup-004"
    assert state["cycles_completed"] == 1
