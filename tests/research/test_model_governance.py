
import pytest
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from research_pipeline.model_governance import ModelGovernance
from model_governance.approval_workflow import ApprovalWorkflow
from model_governance.model_card import ModelCard
from model_governance.champion_challenger import ChampionChallenger
from model_governance.rollback import Rollback
from datetime import datetime, timezone

def _make_entry(mid, status="draft"):
    return ModelEntry(
        model_id=mid, model_version="v1", dataset_id="d1",
        feature_set_id="f1", label_config={},
        training_period="", validation_period="", test_period="",
        metrics={"accuracy": 0.7}, artifact_path="", approval_status=status,
        created_at=datetime.now(timezone.utc).isoformat()
    )

def test_can_trade_only_approved():
    reg = ModelRegistry()
    reg.register(_make_entry("m1", "draft"))
    reg.register(_make_entry("m2", "approved"))
    gov = ModelGovernance(reg)
    assert gov.can_trade("m1") is False
    assert gov.can_trade("m2") is True

def test_enforce_approval():
    reg = ModelRegistry()
    reg.register(_make_entry("m1", "approved"))
    gov = ModelGovernance(reg)
    result = gov.enforce_approval("m1")
    assert result["allowed"] is True

def test_approval_workflow():
    reg = ModelRegistry()
    reg.register(_make_entry("m1", "draft"))
    wf = ApprovalWorkflow(reg)
    wf.submit_for_review("m1")
    assert reg.get("m1").approval_status == "candidate"
    wf.approve("m1", "admin")
    assert reg.get("m1").approval_status == "approved"

def test_model_card():
    reg = ModelRegistry()
    reg.register(_make_entry("m1", "approved"))
    card = ModelCard(reg)
    c = card.generate("m1")
    assert c["model_id"] == "m1"
    assert c["card_version"] == "1.0"

def test_champion_challenger():
    reg = ModelRegistry()
    reg.register(_make_entry("champ", "approved"))
    reg.get("champ").metrics["accuracy"] = 0.6
    reg.register(_make_entry("chall", "candidate"))
    reg.get("chall").metrics["accuracy"] = 0.8
    cc = ChampionChallenger(reg)
    result = cc.compare("champ", "chall", metric_key="accuracy")
    assert result["winner"] == "chall"
    assert result["recommendation"] == "promote challenger"

def test_rollback():
    reg = ModelRegistry()
    reg.register(_make_entry("m1", "approved"))
    reg.get("m1").created_at = "2024-02-01T00:00:00"
    reg.register(_make_entry("m2", "approved"))
    reg.get("m2").created_at = "2024-03-01T00:00:00"
    rb = Rollback(reg)
    result = rb.rollback("m2")
    assert result["rolled_back_to"] == "m1"
    assert result["status"] == "rollback_completed"
