"""Stream health monitoring."""
from typing import Dict, Any
from datetime import datetime, timezone


class StreamHealth:
    def __init__(self, stale_after_seconds: float = 30.0):
        self.stale_after_seconds = stale_after_seconds
        self._last_event_time: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self._events_received = 0
        self._errors = 0
        self._reconnects = 0

    def record_event(self) -> None:
        self._last_event_time = datetime.now(timezone.utc)
        self._events_received += 1

    def record_error(self) -> None:
        self._errors += 1

    def record_reconnect(self) -> None:
        self._reconnects += 1

    def check(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        age = (now - self._last_event_time).total_seconds()
        is_stale = age > self.stale_after_seconds if self._events_received > 0 else False
        return {
            "healthy": not is_stale and self._errors < 10,
            "stale": is_stale,
            "last_event_age_seconds": age,
            "events_received": self._events_received,
            "errors": self._errors,
            "reconnects": self._reconnects,
            "timestamp_utc": now.isoformat(),
        }
