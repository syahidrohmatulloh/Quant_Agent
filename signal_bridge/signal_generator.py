
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService

class SignalGenerator:
    def __init__(self,
                 model_loader: ApprovedModelLoader,
                 feature_runtime: FeatureRuntime,
                 prediction_service: PredictionService):
        self.model_loader = model_loader
        self.feature_runtime = feature_runtime
        self.prediction_service = prediction_service

    def generate(self, model_id: str, data: Any) -> Dict[str, Any]:
        check = self.model_loader.can_generate_signals(model_id)
        if not check["allowed"]:
            return {
                "signal_id": str(uuid.uuid4()),
                "model_id": model_id,
                "approval_status": self.model_loader.registry.get(model_id).approval_status if self.model_loader.registry.get(model_id) else "unknown",
                "generated": False,
                "reason": check["reason"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        model = self.model_loader.load(model_id)
        if not model:
            return {
                "signal_id": str(uuid.uuid4()),
                "model_id": model_id,
                "generated": False,
                "reason": "Model not found or not approved",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        # Compute features
        feat_result = self.feature_runtime.compute(data, model.feature_set_id)
        if not feat_result or not feat_result.get("valid"):
            return {
                "signal_id": str(uuid.uuid4()),
                "model_id": model_id,
                "generated": False,
                "reason": "Feature computation failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        # Predict
        import pandas as pd
        feat_df = pd.DataFrame([feat_result["feature_vector"]])
        pred = self.prediction_service.predict(model_id, feat_df)
        if pred.get("error"):
            return {
                "signal_id": str(uuid.uuid4()),
                "model_id": model_id,
                "generated": False,
                "reason": f"Prediction failed: {pred['error']}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        prediction = pred["prediction"]
        loaded_model = self.prediction_service._models.get(model_id)
        raw_classes = getattr(loaded_model, "classes_", []) if loaded_model is not None else []
        classes = set(raw_classes.tolist() if hasattr(raw_classes, "tolist") else raw_classes)
        # Support both common binary conventions (0/1 and -1/1) without
        # turning a valid class-0 prediction into a nonsensical "hold order".
        # In an explicit three-class model (-1/0/1), class 0 remains HOLD.
        if prediction == 1:
            signal = "buy"
        elif prediction == -1:
            signal = "sell"
        elif prediction == 0 and classes and classes.issubset({0, 1}):
            signal = "sell"
        else:
            signal = "hold"
        return {
            "signal_id": str(uuid.uuid4()),
            "model_id": model_id,
            "model_version": model.model_version,
            "approval_status": model.approval_status,
            "feature_set_id": model.feature_set_id,
            "dataset_id": model.dataset_id,
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": pred["confidence"],
            "signal": signal,
            "generated": True,
            "strategy_id": model.model_id,
            "strategy_version": model.model_version
        }
