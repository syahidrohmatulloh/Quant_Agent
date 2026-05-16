
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

class ExperimentTracker:
    def __init__(self):
        self.experiments: Dict[str, Dict[str, Any]] = {}

    def start(self, name: str, params: Dict[str, Any]) -> str:
        exp_id = str(uuid.uuid4())
        self.experiments[exp_id] = {
            "exp_id": exp_id,
            "name": name,
            "params": params,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None,
            "metrics": {},
            "artifacts": []
        }
        return exp_id

    def log_metric(self, exp_id: str, key: str, value: Any):
        if exp_id in self.experiments:
            self.experiments[exp_id]["metrics"][key] = value

    def log_artifact(self, exp_id: str, path: str):
        if exp_id in self.experiments:
            self.experiments[exp_id]["artifacts"].append(path)

    def end(self, exp_id: str, status: str = "completed"):
        if exp_id in self.experiments:
            self.experiments[exp_id]["status"] = status
            self.experiments[exp_id]["ended_at"] = datetime.now(timezone.utc).isoformat()

    def get(self, exp_id: str) -> Dict[str, Any]:
        return self.experiments.get(exp_id, {})
