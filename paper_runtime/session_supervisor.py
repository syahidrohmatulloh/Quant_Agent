"""Session supervisor for long-running paper sessions."""
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .reconnect_policy import ReconnectPolicy
from .paper_runtime_state import PaperRuntimeState
from .runtime_recorder import RuntimeRecorder


class SessionSupervisor:
    def __init__(
        self,
        session_id: str = "",
        max_failures: int = 10,
        reconnect_policy: Optional[ReconnectPolicy] = None,
        recorder: Optional[RuntimeRecorder] = None,
    ):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.max_failures = max_failures
        self.reconnect_policy = reconnect_policy or ReconnectPolicy()
        self.recorder = recorder
        self.state = PaperRuntimeState(session_id=self.session_id, max_failures=max_failures)
        self._running = False
        self._start_time: Optional[float] = None

    def start(self) -> None:
        self._running = True
        self._start_time = time.time()
        self.state.status = "running"
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        if self.recorder:
            self.recorder.record_alert(f"Session {self.session_id} started")

    def stop(self) -> None:
        self._running = False
        self.state.status = "stopped"
        self.state.stopped_at = datetime.now(timezone.utc).isoformat()
        if self.recorder:
            self.recorder.record_alert(f"Session {self.session_id} stopped")
            self.recorder.flush()

    def is_running(self) -> bool:
        return self._running

    def record_cycle(self, success: bool, reason: str = "") -> None:
        if success:
            self.state.cycles_completed += 1
            self.state.failure_count = 0
        else:
            self.state.cycles_skipped += 1
            self.state.failure_count += 1
            if reason:
                self.state.alerts.append(reason)
            if self.recorder:
                self.recorder.record_alert(f"Cycle failed: {reason}")

        if self.state.failure_count >= self.max_failures:
            self.state.status = "error"
            self._running = False
            if self.recorder:
                self.recorder.record_alert(f"Max failures ({self.max_failures}) reached. Session stopped.")
                self.recorder.flush()

    def update_heartbeat(self) -> None:
        self.state.heartbeat = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": self.uptime_seconds(),
            "cycles_completed": self.state.cycles_completed,
            "cycles_skipped": self.state.cycles_skipped,
            "failure_count": self.state.failure_count,
            "status": self.state.status,
        }

    def uptime_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def export_state(self) -> Dict[str, Any]:
        return self.state.to_dict()
