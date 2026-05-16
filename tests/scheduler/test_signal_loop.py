
import pytest
import pandas as pd
from scheduler.signal_loop import SignalLoop
from live_data.csv_replay_adapter import CSVReplayAdapter
from live_data.data_quality_monitor import DataQualityMonitor
from live_data.market_clock import MarketClock

class AlwaysTradingClock(MarketClock):
    def is_trading_window(self, dt=None):
        return True
    def is_weekend(self, dt=None):
        return False
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from signal_bridge.signal_generator import SignalGenerator
from signal_bridge.signal_router import SignalRouter
from signal_bridge.paper_signal_executor import PaperSignalExecutor
from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.audit import AuditLogger
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec
from datetime import datetime, timezone
import tempfile
import json
import os

def _make_loop(data_path: str, approved: bool = True, circuit: bool = False, min_confidence: float = 0.0):
    adapter = CSVReplayAdapter(data_path)
    adapter.connect()
    reg = ModelRegistry()
    if approved:
        entry = ModelEntry(
            model_id="m1", model_version="v1", dataset_id="d1",
            feature_set_id="returns_v1", label_config={},
            training_period="", validation_period="", test_period="",
            metrics={}, artifact_path="", approval_status="approved",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        reg.register(entry)
    freg = FeatureRegistry()
    freg.register(FeatureSpec("returns", "v1", "pct_change", 1, ["close"]), lambda df: df["close"].pct_change())
    svc = PredictionService()
    from research_pipeline.model_trainer import SimpleRuleModel
    model = SimpleRuleModel(feature_weights={"returns_v1": 1.0})
    svc.load_model("m1", model)
    tmpdir = tempfile.mkdtemp()
    return SignalLoop(
        data_adapter=adapter,
        data_quality=DataQualityMonitor(),
        market_clock=AlwaysTradingClock(),
        model_loader=ApprovedModelLoader(reg),
        feature_runtime=FeatureRuntime(freg),
        prediction_service=svc,
        signal_generator=SignalGenerator(
            ApprovedModelLoader(reg), FeatureRuntime(freg), svc
        ),
        signal_router=SignalRouter(),
        paper_executor=PaperSignalExecutor(
            PaperBroker(), RiskManager(), AuditLogger(os.path.join(tmpdir, "audit.jsonl")),
            circuit_breaker=circuit
        ),
        min_confidence=min_confidence
    )

def test_signal_loop_runs_cycle():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002, "close": 1.1001}], f)
        path = f.name
    try:
        loop = _make_loop(path)
        result = loop.run_cycle("EURUSD")
        assert "cycle_id" in result
    finally:
        os.unlink(path)

def test_rejects_circuit_breaker():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}], f)
        path = f.name
    try:
        loop = _make_loop(path, circuit=True)
        result = loop.run_cycle("EURUSD")
        assert result["executed"] is False
        assert result["reason"] == "circuit_breaker_open"
    finally:
        os.unlink(path)

def test_rejects_unapproved_model():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"symbol": "EURUSD", "bid": 1.1, "ask": 1.1002}], f)
        path = f.name
    try:
        loop = _make_loop(path, approved=False)
        result = loop.run_cycle("EURUSD")
        assert result["executed"] is False
        assert result["reason"] == "no_approved_model"
    finally:
        os.unlink(path)

def test_rejects_low_confidence():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([
            {"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002, "close": 1.1001},
            {"symbol": "EURUSD", "bid": 1.1001, "ask": 1.1003, "close": 1.1002},
            {"symbol": "EURUSD", "bid": 1.1002, "ask": 1.1004, "close": 1.1003},
            {"symbol": "EURUSD", "bid": 1.1003, "ask": 1.1005, "close": 1.1004},
            {"symbol": "EURUSD", "bid": 1.1004, "ask": 1.1006, "close": 1.1005},
            {"symbol": "EURUSD", "bid": 1.1005, "ask": 1.1007, "close": 1.1006}
        ], f)
        path = f.name
    try:
        loop = _make_loop(path, min_confidence=0.99)
        result = loop.run_cycle("EURUSD")
        assert result["executed"] is False
        assert result["reason"] == "low_confidence"
    finally:
        os.unlink(path)

def test_rejects_data_quality_failure():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        # Stale timestamp (old) to trigger data quality failure
        json.dump([{"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002, "close": 1.1001, "timestamp": "2020-01-01T00:00:00"}], f)
        path = f.name
    try:
        loop = _make_loop(path)
        result = loop.run_cycle("EURUSD")
        assert result["executed"] is False
        assert result["reason"] == "data_quality_failed"
    finally:
        os.unlink(path)

def test_paper_executor_called():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([
            {"symbol": "EURUSD", "bid": 1.1000, "ask": 1.1002, "close": 1.1001},
            {"symbol": "EURUSD", "bid": 1.1001, "ask": 1.1003, "close": 1.1002},
            {"symbol": "EURUSD", "bid": 1.1002, "ask": 1.1004, "close": 1.1003},
            {"symbol": "EURUSD", "bid": 1.1003, "ask": 1.1005, "close": 1.1004},
            {"symbol": "EURUSD", "bid": 1.1004, "ask": 1.1006, "close": 1.1005},
            {"symbol": "EURUSD", "bid": 1.1005, "ask": 1.1007, "close": 1.1006}
        ], f)
        path = f.name
    try:
        loop = _make_loop(path)
        result = loop.run_cycle("EURUSD")
        assert result["executed"] is True
        assert result["destination"] == "paper"
    finally:
        os.unlink(path)
