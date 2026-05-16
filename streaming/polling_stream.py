"""Generic polling stream implementation."""
import time
from typing import Dict, Any, Optional, Iterator, Callable
from datetime import datetime, timezone

from .stream_event import StreamEvent, tick_event, heartbeat_event, error_event
from .stream_health import StreamHealth
from .stream_supervisor import StreamSupervisor


class PollingStream:
    """Generic polling stream that calls a fetch function at intervals."""

    def __init__(
        self,
        fetch_fn: Callable[[str], Optional[Dict[str, Any]]],
        poll_interval_seconds: float = 5.0,
        max_events: int = 0,
        supervisor: Optional[StreamSupervisor] = None,
    ):
        self.fetch_fn = fetch_fn
        self.poll_interval = poll_interval_seconds
        self.max_events = max_events
        self.supervisor = supervisor
        self._running = False

    def start(self, symbol: str = "EURUSD") -> Iterator[StreamEvent]:
        self._running = True
        event_count = 0
        while self._running:
            if self.max_events > 0 and event_count >= self.max_events:
                break
            try:
                raw = self.fetch_fn(symbol)
                if raw:
                    event = tick_event(
                        symbol=raw.get("symbol", symbol),
                        bid=raw.get("bid", 0),
                        ask=raw.get("ask", 0),
                        source=raw.get("source", "polling"),
                    )
                    yield event.to_dict()
                    event_count += 1
                    if self.supervisor:
                        self.supervisor.record_event()
                else:
                    yield heartbeat_event().to_dict()
            except Exception as e:
                yield error_event(str(e)).to_dict()
                if self.supervisor:
                    self.supervisor.record_error(str(e))
            if self._running:
                time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
