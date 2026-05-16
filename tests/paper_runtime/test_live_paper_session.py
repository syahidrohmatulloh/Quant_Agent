"""Tests for live paper session."""
import pytest
from unittest.mock import MagicMock

from paper_runtime.live_paper_session import LivePaperSession
from paper_runtime.session_supervisor import SessionSupervisor
from paper_runtime.runtime_recorder import RuntimeRecorder
from broker_integration.oanda.oanda_practice_adapter import OandaPracticeAdapter
from broker_integration.broker_config import BrokerConfig


def make_mock_broker(healthy=True, tick=None, snapshot=None):
    config = BrokerConfig(broker_name="mock", environment="paper")
    broker = MagicMock(spec=OandaPracticeAdapter)
    broker.health_check.return_value = {"healthy": healthy, "reason": "" if healthy else "test"}
    broker.get_latest_tick.return_value = tick or {
        "symbol": "EURUSD", "timestamp_utc": "2024-01-01T00:00:00Z",
        "bid": 1.1000, "ask": 1.10005, "mid": 1.100025, "spread": 0.00005, "volume": 0, "source": "mock"
    }
    broker.get_account_snapshot.return_value = snapshot or {
        "cash": 100000, "equity": 100000, "currency": "USD", "open_positions": [], "open_orders": []
    }
    broker.broker_name = "mock"
    broker.environment = "paper"
    return broker


def test_one_cycle_passes():
    broker = make_mock_broker()
    supervisor = SessionSupervisor(session_id="test-001")
    recorder = RuntimeRecorder("/tmp/test_reports", "test-001")
    session = LivePaperSession(broker, supervisor, recorder=recorder)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is True
    assert "audit" in result
    supervisor.stop()


def test_unhealthy_broker_skips_cycle():
    broker = make_mock_broker(healthy=False)
    supervisor = SessionSupervisor(session_id="test-002")
    session = LivePaperSession(broker, supervisor)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is False
    assert any("broker_unhealthy" in r for r in result["reasons"])
    supervisor.stop()


def test_stale_tick_skips_signal():
    from datetime import datetime, timezone
    old_tick = {
        "symbol": "EURUSD", "timestamp_utc": "2020-01-01T00:00:00Z",
        "bid": 1.1, "ask": 1.1005, "mid": 1.10025, "spread": 0.0005, "volume": 0, "source": "mock"
    }
    broker = make_mock_broker(tick=old_tick)
    supervisor = SessionSupervisor(session_id="test-003")
    session = LivePaperSession(broker, supervisor)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is False
    assert any("stale_tick" in r for r in result["reasons"])
    supervisor.stop()


def test_wide_spread_skips_signal():
    wide_tick = {
        "symbol": "EURUSD", "timestamp_utc": "2024-01-01T00:00:00Z",
        "bid": 1.1, "ask": 1.2, "mid": 1.15, "spread": 0.1, "volume": 0, "source": "mock"
    }
    broker = make_mock_broker(tick=wide_tick)
    supervisor = SessionSupervisor(session_id="test-004")
    session = LivePaperSession(broker, supervisor, max_spread=0.01)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is False
    assert any("wide_spread" in r for r in result["reasons"])
    supervisor.stop()


def test_unapproved_model_rejects_signal():
    broker = make_mock_broker()
    supervisor = SessionSupervisor(session_id="test-005")
    model_loader = MagicMock()
    model_loader.load_approved.return_value = None
    session = LivePaperSession(broker, supervisor, model_loader=model_loader)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is False
    assert any("unapproved_model" in r for r in result["reasons"])
    supervisor.stop()


def test_reconciliation_mismatch_pauses_session():
    broker = make_mock_broker()
    broker.get_account_snapshot.return_value = {
        "cash": 99999, "equity": 99999, "currency": "USD",
        "open_positions": [{"symbol": "EURUSD", "volume": 1, "entry_price": 1.1}],
        "open_orders": []
    }
    supervisor = SessionSupervisor(session_id="test-006")
    session = LivePaperSession(broker, supervisor)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is False
    assert any("reconciliation_severe" in r for r in result["reasons"])
    assert supervisor.state.status == "paused"
    supervisor.stop()


def test_no_live_order_path():
    broker = make_mock_broker()
    supervisor = SessionSupervisor(session_id="test-007")
    session = LivePaperSession(broker, supervisor)
    supervisor.start()
    result = session.run_cycle("EURUSD")
    assert result["cycle_executed"] is True
    # Verify no live order was submitted
    broker.submit_paper_order.assert_not_called()
    supervisor.stop()
