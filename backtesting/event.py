
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

@dataclass(frozen=True)
class MarketEvent:
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    extra: Dict[str, Any] = None

@dataclass(frozen=True)
class SignalEvent:
    timestamp: datetime
    symbol: str
    signal: str  # buy / sell / close
    meta: Dict[str, Any] = None

@dataclass(frozen=True)
class OrderEvent:
    timestamp: datetime
    symbol: str
    direction: str
    volume: float
    order_type: str = "market"
    sl: float = None
    tp: float = None

@dataclass(frozen=True)
class FillEvent:
    timestamp: datetime
    symbol: str
    direction: str
    volume: float
    fill_price: float
    commission: float
    order_id: str = ""

@dataclass(frozen=True)
class PositionClosedEvent:
    timestamp: datetime
    symbol: str
    direction: str
    volume: float
    entry_price: float
    exit_price: float
    pnl: float
    commission: float
