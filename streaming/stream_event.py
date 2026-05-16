from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
import uuid


@dataclass
class StreamEvent:
    event_type: str = "tick"
    symbol: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "stream"
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "symbol": self.symbol,
            "timestamp_utc": self.timestamp_utc,
            "payload": self.payload,
            "source": self.source,
        }


def tick_event(symbol: str, bid: float, ask: float, source: str = "oanda_practice") -> StreamEvent:
    bid = float(bid)
    ask = float(ask)
    mid = round((bid + ask) / 2, 10) if bid and ask else 0
    spread = round(ask - bid, 10) if ask and bid else 0

    payload = {
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread": spread,
    }

    return StreamEvent(
        event_type="tick",
        symbol=symbol,
        payload=payload,
        source=source,
    )


def heartbeat_event(source: str = "stream") -> StreamEvent:
    return StreamEvent(
        event_type="heartbeat",
        payload={"status": "ok"},
        source=source,
    )


def error_event(error: str, source: str = "stream") -> StreamEvent:
    return StreamEvent(
        event_type="error",
        payload={"error": str(error)},
        source=source,
    )
