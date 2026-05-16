
from typing import Dict, Any
from research_pipeline.model_registry import ModelRegistry, ModelEntry

class ModelCard:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def generate(self, model_id: str) -> Dict[str, Any]:
        m = self.registry.get(model_id)
        if not m:
            return {"error": "Model not found"}
        return {
            "model_id": m.model_id,
            "model_version": m.model_version,
            "dataset_id": m.dataset_id,
            "feature_set_id": m.feature_set_id,
            "label_config": m.label_config,
            "training_period": m.training_period,
            "validation_period": m.validation_period,
            "test_period": m.test_period,
            "metrics": m.metrics,
            "approval_status": m.approval_status,
            "approved_by": m.approved_by,
            "approval_notes": m.approval_notes,
            "created_at": m.created_at,
            "card_version": "1.0"
        }
