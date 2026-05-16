
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from research_pipeline.model_trainer import ModelTrainer, SimpleRuleModel

class PredictionService:
    def __init__(self, model_trainer: Optional[ModelTrainer] = None):
        self.trainer = model_trainer or ModelTrainer()
        self._models: Dict[str, Any] = {}

    def load_model(self, model_id: str, artifact: Any):
        self._models[model_id] = artifact

    def predict(self, model_id: str, features: pd.DataFrame,
                expected_schema: Optional[List[str]] = None) -> Dict[str, Any]:
        if model_id not in self._models:
            return {"error": "Model not loaded", "prediction": None, "confidence": 0.0}
        # Schema check
        if expected_schema:
            missing = [c for c in expected_schema if c not in features.columns]
            if missing:
                return {"error": f"Schema mismatch: missing {missing}", "prediction": None, "confidence": 0.0}
        model = self._models[model_id]
        # If it's a SimpleRuleModel or sklearn model
        if hasattr(model, "predict"):
            preds = model.predict(features)
            conf = np.ones(len(preds)) * 0.5
            if hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(features)
                    conf = proba.max(axis=1)
                except Exception:
                    pass
            return {
                "prediction": int(preds[0]) if len(preds) > 0 else None,
                "confidence": round(float(conf[0]), 4) if len(conf) > 0 else 0.0,
                "raw_score": float(preds[0]) if len(preds) > 0 else 0.0,
                "model_id": model_id,
                "model_version": getattr(model, "version", "v1")
            }
        return {"error": "Model has no predict method", "prediction": None, "confidence": 0.0}

    def is_available(self, model_id: str) -> bool:
        return model_id in self._models
