
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class JobStore:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def add(self, job_id: str, job_type: str, params: Dict[str, Any]) -> str:
        self.jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "params": params,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        return job_id

    def start(self, job_id: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["started_at"] = datetime.now(timezone.utc).isoformat()

    def complete(self, job_id: str, result: Any):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.jobs[job_id]["result"] = result

    def fail(self, job_id: str, error: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.jobs[job_id]["error"] = error

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_jobs = sorted(self.jobs.values(), key=lambda x: x.get("created_at", ""), reverse=True)
        return sorted_jobs[:limit]
