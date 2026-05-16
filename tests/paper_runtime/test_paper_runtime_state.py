"""Tests for paper runtime state."""
from paper_runtime.paper_runtime_state import PaperRuntimeState


def test_state_initialization():
    state = PaperRuntimeState(session_id="state-001")
    assert state.session_id == "state-001"
    assert state.status == "idle"
    assert state.cycles_completed == 0
    assert state.started_at != ""


def test_state_to_dict():
    state = PaperRuntimeState(session_id="state-002")
    d = state.to_dict()
    assert d["session_id"] == "state-002"
    assert "started_at" in d
