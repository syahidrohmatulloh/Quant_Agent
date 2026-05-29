"""
Append-only audit log for paper orchestration workflow.
Never includes credentials or API tokens.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditLog:
    """Append-only JSONL audit log."""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, run_id: str, details: Dict[str, Any] = None) -> None:
        record = {
            "timestamp": _now_iso(),
            "event_type": event_type,
            "run_id": run_id,
            "details": details or {},
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        records = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records
