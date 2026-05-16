"""Stream supervisor for long-running market data streams."""
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .stream_health import StreamHealth
from .stream_reconnect import StreamReconnectPolicy


class StreamSupervisor:
    def __init__(
        self,
        stream_id: str = "",
        health: Optional[StreamHealth] = None,
        reconnect_policy: Optional[StreamReconnectPolicy] = None,
        max_errors: int = 10,
    ):
        self.stream_id = stream_id or "default"
        self.health = health or StreamHealth()
        self.reconnect_policy = reconnect_policy or StreamReconnectPolicy()
        self.max_errors = max_errors
        self._running = False
        self._start_time: Optional[float] = None
        self._error_count = 0
        self._reconnect_count = 0

    def start(self) -> None:
        self._running = True
        self._start_time = time.time()

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def record_event(self) -> None:
        self.health.record_event()

    def record_error(self, reason: str = "") -> None:
        self.health.record_error()
        self._error_count += 1
        if self._error_count >= self.max_errors:
            self._running = False

    def record_reconnect(self) -> None:
        self.health.record_reconnect()
        self._reconnect_count += 1
        if self._reconnect_count >= self.reconnect_policy.max_reconnect_attempts:
            self._running = False

    def uptime_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def status(self) -> Dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "running": self._running,
            "uptime_seconds": self.uptime_seconds(),
            "error_count": self._error_count,
            "reconnect_count": self._reconnect_count,
            "health": self.health.check(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
