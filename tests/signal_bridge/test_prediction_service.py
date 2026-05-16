
import pytest
import pandas as pd
import numpy as np
from research_pipeline.model_trainer import SimpleRuleModel
from signal_bridge.prediction_service import PredictionService

def test_prediction_success():
    svc = PredictionService()
    model = SimpleRuleModel()
    model.feature_weights = {"feat1": 1.0}
    svc.load_model("m1", model)
    df = pd.DataFrame({"feat1": [1.0, -1.0]})
    result = svc.predict("m1", df)
    assert result["prediction"] is not None
    assert "confidence" in result
    assert "model_id" in result

def test_missing_model_fails_closed():
    svc = PredictionService()
    df = pd.DataFrame({"feat1": [1.0]})
    result = svc.predict("missing", df)
    assert result["prediction"] is None
    assert "error" in result

def test_schema_mismatch_fails_closed():
    svc = PredictionService()
    model = SimpleRuleModel()
    model.feature_weights = {"feat1": 1.0}
    svc.load_model("m1", model)
    df = pd.DataFrame({"feat2": [1.0]})
    result = svc.predict("m1", df, expected_schema=["feat1"])
    assert result["prediction"] is None
    assert "Schema mismatch" in result["error"]

def test_deterministic_prediction():
    svc = PredictionService()
    model = SimpleRuleModel()
    model.feature_weights = {"feat1": 1.0}
    svc.load_model("m1", model)
    df = pd.DataFrame({"feat1": [1.0]})
    r1 = svc.predict("m1", df)
    r2 = svc.predict("m1", df)
    assert r1["prediction"] == r2["prediction"]
    assert r1["confidence"] == r2["confidence"]
