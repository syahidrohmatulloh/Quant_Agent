
from typing import Dict, Any, Optional, List
from research_pipeline.model_registry import ModelRegistry, ModelEntry

class ModelGovernance:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def can_trade(self, model_id: str) -> bool:
        m = self.registry.get(model_id)
        if not m:
            return False
        return m.approval_status == "approved"

    def enforce_approval(self, model_id: str) -> Dict[str, Any]:
        allowed = self.can_trade(model_id)
        return {
            "model_id": model_id,
            "allowed": allowed,
            "reason": "Model approved" if allowed else "Model not approved for trading"
        }

    def list_tradable(self) -> List[ModelEntry]:
        return self.registry.list_by_status("approved")

    def audit_model_usage(self, model_id: str, signal_count: int = 0) -> Dict[str, Any]:
        return {
            "model_id": model_id,
            "signal_count": signal_count,
            "governance_check": self.enforce_approval(model_id)
        }
