
from typing import Dict, Any, Optional, List
from research_pipeline.model_registry import ModelRegistry, ModelEntry

class ApprovedModelLoader:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def load(self, model_id: str) -> Optional[ModelEntry]:
        m = self.registry.get(model_id)
        if not m:
            return None
        if m.approval_status != "approved":
            return None
        return m

    def list_approved(self) -> List[ModelEntry]:
        return self.registry.list_by_status("approved")

    def can_generate_signals(self, model_id: str) -> Dict[str, Any]:
        m = self.registry.get(model_id)
        if not m:
            return {"allowed": False, "reason": "Model not found"}
        if m.approval_status == "draft":
            return {"allowed": False, "reason": "Draft model cannot generate signals"}
        if m.approval_status == "candidate":
            return {"allowed": False, "reason": "Candidate model cannot generate signals"}
        if m.approval_status == "rejected":
            return {"allowed": False, "reason": "Rejected model cannot generate signals"}
        if m.approval_status == "archived":
            return {"allowed": False, "reason": "Archived model cannot generate signals"}
        if m.approval_status == "approved":
            return {"allowed": True, "reason": "Model approved for signal generation"}
        return {"allowed": False, "reason": f"Unknown status: {m.approval_status}"}
