
from typing import Dict, Any, Optional
from research_pipeline.model_registry import ModelRegistry, ModelEntry

class Rollback:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def rollback(self, from_model_id: str) -> Dict[str, Any]:
        current = self.registry.get(from_model_id)
        if not current:
            return {"error": "Model not found"}
        # Find previous approved model excluding current
        approved = [m for m in self.registry.list_by_status("approved") if m.model_id != from_model_id]
        if not approved:
            return {"error": "No previous approved model to rollback to"}
        previous = max(approved, key=lambda x: x.created_at)
        return {
            "rolled_back_from": from_model_id,
            "rolled_back_to": previous.model_id,
            "previous_model_version": previous.model_version,
            "status": "rollback_completed"
        }
