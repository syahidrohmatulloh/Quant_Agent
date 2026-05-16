
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class Heartbeat:
    def __init__(self, component: str = "scheduler"):
        self.component = component
        self.heartbeat_id = str(uuid.uuid4())
        self.last_beat: Optional[str] = None
        self.status = "unknown"
        self.metadata: Dict[str, Any] = {}

    def beat(self, status: str = "ok", metadata: Optional[Dict[str, Any]] = None):
        self.last_beat = datetime.now(timezone.utc).isoformat()
        self.status = status
        if metadata:
            self.metadata.update(metadata)

    def is_stale(self, max_age_seconds: float = 60.0) -> bool:
        if not self.last_beat:
            return True
        try:
            last = datetime.fromisoformat(self.last_beat.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - last).total_seconds() > max_age_seconds
        except Exception:
            return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "heartbeat_id": self.heartbeat_id,
            "last_beat": self.last_beat,
            "status": self.status,
            "metadata": self.metadata
        }
