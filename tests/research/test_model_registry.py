
import pytest
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from datetime import datetime, timezone

def test_register_and_get():
    reg = ModelRegistry()
    entry = ModelEntry(
        model_id="m1", model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={"method": "direction"},
        training_period="2024-01-01/2024-02-01",
        validation_period="2024-02-01/2024-03-01",
        test_period="2024-03-01/2024-04-01",
        metrics={"accuracy": 0.6}, artifact_path="/tmp/m1.pkl",
        approval_status="draft", created_at=datetime.now(timezone.utc).isoformat()
    )
    reg.register(entry)
    assert reg.get("m1") is not None
    assert reg.get("m1").model_id == "m1"

def test_approve():
    reg = ModelRegistry()
    entry = ModelEntry(
        model_id="m1", model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status="draft",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    reg.register(entry)
    assert reg.approve("m1", "admin", "looks good")
    assert reg.get("m1").approval_status == "approved"
    assert reg.get("m1").approved_by == "admin"

def test_reject():
    reg = ModelRegistry()
    entry = ModelEntry(
        model_id="m1", model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status="candidate",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    reg.register(entry)
    reg.reject("m1", "underperforms")
    assert reg.get("m1").approval_status == "rejected"

def test_list_by_status():
    reg = ModelRegistry()
    for i, status in enumerate(["draft", "approved", "approved"]):
        entry = ModelEntry(
            model_id=f"m{i}", model_version="v1", dataset_id="d1",
            feature_set_id="f1", label_config={},
            training_period="", validation_period="", test_period="",
            metrics={}, artifact_path="", approval_status=status,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        reg.register(entry)
    assert len(reg.list_by_status("approved")) == 2

def test_get_latest_approved():
    reg = ModelRegistry()
    entry1 = ModelEntry(
        model_id="m1", model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status="approved",
        created_at="2024-01-01T00:00:00"
    )
    entry2 = ModelEntry(
        model_id="m2", model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={}, artifact_path="", approval_status="approved",
        created_at="2024-02-01T00:00:00"
    )
    reg.register(entry1)
    reg.register(entry2)
    latest = reg.get_latest_approved()
    assert latest.model_id == "m2"
