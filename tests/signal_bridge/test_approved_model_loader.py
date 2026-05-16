
import pytest
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from signal_bridge.approved_model_loader import ApprovedModelLoader
from datetime import datetime, timezone

def _entry(mid, status="draft"):
    return ModelEntry(
        model_id=mid, model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status=status,
        created_at=datetime.now(timezone.utc).isoformat()
    )

def test_load_approved_model():
    reg = ModelRegistry()
    reg.register(_entry("m1", "approved"))
    loader = ApprovedModelLoader(reg)
    assert loader.load("m1") is not None
    assert loader.load("m1").approval_status == "approved"

def test_reject_draft():
    reg = ModelRegistry()
    reg.register(_entry("m1", "draft"))
    loader = ApprovedModelLoader(reg)
    assert loader.load("m1") is None

def test_reject_candidate():
    reg = ModelRegistry()
    reg.register(_entry("m1", "candidate"))
    loader = ApprovedModelLoader(reg)
    assert loader.load("m1") is None

def test_reject_rejected():
    reg = ModelRegistry()
    reg.register(_entry("m1", "rejected"))
    loader = ApprovedModelLoader(reg)
    assert loader.load("m1") is None

def test_reject_archived():
    reg = ModelRegistry()
    reg.register(_entry("m1", "archived"))
    loader = ApprovedModelLoader(reg)
    assert loader.load("m1") is None

def test_can_generate_signals_approved():
    reg = ModelRegistry()
    reg.register(_entry("m1", "approved"))
    loader = ApprovedModelLoader(reg)
    result = loader.can_generate_signals("m1")
    assert result["allowed"] is True

def test_can_generate_signals_all_statuses():
    reg = ModelRegistry()
    for status in ["draft", "candidate", "rejected", "archived"]:
        reg.register(_entry(status, status))
        loader = ApprovedModelLoader(reg)
        result = loader.can_generate_signals(status)
        assert result["allowed"] is False
