"""Paper runtime state tracking."""
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime, timezone


@dataclass
class PaperRuntimeState:
    session_id: str
    started_at: str = ""
    stopped_at: str = ""
    cycles_completed: int = 0
    cycles_skipped: int = 0
    failure_count: int = 0
    max_failures: int = 10
    status: str = "idle"  # idle, running, paused, stopped, error
    last_tick: Dict[str, Any] = field(default_factory=dict)
    last_signal: Dict[str, Any] = field(default_factory=dict)
    last_rejection: Dict[str, Any] = field(default_factory=dict)
    last_snapshot: Dict[str, Any] = field(default_factory=dict)
    last_reconciliation: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    heartbeat: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "cycles_completed": self.cycles_completed,
            "cycles_skipped": self.cycles_skipped,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "status": self.status,
            "last_tick": self.last_tick,
            "last_signal": self.last_signal,
            "last_rejection": self.last_rejection,
            "last_snapshot": self.last_snapshot,
            "last_reconciliation": self.last_reconciliation,
            "alerts": self.alerts,
            "heartbeat": self.heartbeat,
        }
