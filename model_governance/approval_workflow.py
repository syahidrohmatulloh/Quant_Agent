
from typing import Dict, Any, Optional
from research_pipeline.model_registry import ModelRegistry

class ApprovalWorkflow:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def submit_for_review(self, model_id: str) -> Dict[str, Any]:
        m = self.registry.get(model_id)
        if not m:
            return {"error": "Model not found"}
        if m.approval_status != "draft":
            return {"error": f"Model status is {m.approval_status}, expected draft"}
        m.approval_status = "candidate"
        return {"model_id": model_id, "status": "candidate", "message": "Submitted for review"}

    def approve(self, model_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        m = self.registry.get(model_id)
        if not m:
            return {"error": "Model not found"}
        if m.approval_status not in ("candidate", "draft"):
            return {"error": f"Cannot approve from status {m.approval_status}"}
        success = self.registry.approve(model_id, approver, notes)
        return {"model_id": model_id, "status": "approved", "approved_by": approver, "notes": notes}

    def reject(self, model_id: str, notes: str = "") -> Dict[str, Any]:
        m = self.registry.get(model_id)
        if not m:
            return {"error": "Model not found"}
        self.registry.reject(model_id, notes)
        return {"model_id": model_id, "status": "rejected", "notes": notes}
