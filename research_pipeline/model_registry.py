
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class ModelEntry:
    model_id: str
    model_version: str
    dataset_id: str
    feature_set_id: str
    label_config: Dict[str, Any]
    training_period: str
    validation_period: str
    test_period: str
    metrics: Dict[str, Any]
    artifact_path: str
    approval_status: str  # draft / candidate / approved / rejected / archived
    created_at: str
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}

    def register(self, entry: ModelEntry) -> str:
        self._models[entry.model_id] = entry
        return entry.model_id

    def get(self, model_id: str) -> Optional[ModelEntry]:
        return self._models.get(model_id)

    def list_by_status(self, status: str) -> List[ModelEntry]:
        return [m for m in self._models.values() if m.approval_status == status]

    def approve(self, model_id: str, approved_by: str, notes: str = "") -> bool:
        m = self._models.get(model_id)
        if not m:
            return False
        m.approval_status = "approved"
        m.approved_by = approved_by
        m.approval_notes = notes
        return True

    def reject(self, model_id: str, notes: str = "") -> bool:
        m = self._models.get(model_id)
        if not m:
            return False
        m.approval_status = "rejected"
        m.approval_notes = notes
        return True

    def archive(self, model_id: str) -> bool:
        m = self._models.get(model_id)
        if not m:
            return False
        m.approval_status = "archived"
        return True

    def get_latest_approved(self) -> Optional[ModelEntry]:
        approved = [m for m in self._models.values() if m.approval_status == "approved"]
        if not approved:
            return None
        return max(approved, key=lambda x: x.created_at)

    def to_dict(self) -> Dict[str, Any]:
        return {k: asdict(v) for k, v in self._models.items()}
