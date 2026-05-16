
import pytest
import pandas as pd
import numpy as np
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec
from research_pipeline.model_trainer import SimpleRuleModel
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from signal_bridge.signal_generator import SignalGenerator
from datetime import datetime, timezone

def _make_registry(status="approved"):
    reg = ModelRegistry()
    entry = ModelEntry(
        model_id="m1", model_version="v1", dataset_id="d1",
        feature_set_id="returns_v1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status=status,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    reg.register(entry)
    return reg

def _make_generator(status="approved"):
    reg = _make_registry(status)
    loader = ApprovedModelLoader(reg)
    freg = FeatureRegistry()
    freg.register(FeatureSpec("returns", "v1", "pct_change", 5, ["close"]), lambda df: df["close"].pct_change())
    runtime = FeatureRuntime(freg)
    svc = PredictionService()
    model = SimpleRuleModel()
    model.feature_weights = {"returns_v1": 1.0}
    svc.load_model("m1", model)
    return SignalGenerator(loader, runtime, svc)

def test_approved_model_generates_signal():
    gen = _make_generator("approved")
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = gen.generate("m1", data)
    assert result["generated"] is True
    assert result["approval_status"] == "approved"
    assert "signal_id" in result
    assert "confidence" in result

def test_draft_model_rejected():
    gen = _make_generator("draft")
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = gen.generate("m1", data)
    assert result["generated"] is False
    assert "Draft model" in result["reason"]

def test_rejected_model_rejected():
    gen = _make_generator("rejected")
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = gen.generate("m1", data)
    assert result["generated"] is False

def test_signal_includes_required_fields():
    gen = _make_generator("approved")
    data = pd.DataFrame({"close": np.arange(20, dtype=float)})
    result = gen.generate("m1", data)
    assert result["generated"] is True
    assert "model_id" in result
    assert "model_version" in result
    assert "feature_set_id" in result
    assert "dataset_id" in result
    assert "prediction_timestamp" in result
    assert "strategy_id" in result
    assert "strategy_version" in result
