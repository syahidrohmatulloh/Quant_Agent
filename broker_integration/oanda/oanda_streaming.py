"""OANDA practice streaming/polling market data."""
import time
from typing import Dict, Any, Optional, Iterator
from datetime import datetime, timezone

from broker_integration.broker_config import BrokerConfig
from broker_integration.transport.network_errors import TransportError
from .oanda_http_transport import OandaHttpTransport
from .oanda_instruments import to_oanda_symbol


class OandaPollingStream:
    """Polling-based market data stream for OANDA practice.

    Polls latest prices at configurable intervals.
    Safe for testing — no persistent connection required.
    """

    def __init__(
        self,
        config: BrokerConfig,
        transport: Optional[OandaHttpTransport] = None,
        poll_interval_seconds: float = 5.0,
        max_events: int = 0,  # 0 = unlimited
    ):
        self.config = config
        self.transport = transport
        self.poll_interval = poll_interval_seconds
        self.max_events = max_events
        self._running = False
        self._event_count = 0

    def start(self, symbol: str = "EUR_USD") -> Iterator[Dict[str, Any]]:
        self._running = True
        self._event_count = 0
        instrument = to_oanda_symbol(symbol)
        account_id = self.config.account_id or ""
        while self._running:
            if self.max_events > 0 and self._event_count >= self.max_events:
                break
            try:
                if self.transport and account_id:
                    result = self.transport.get_latest_price(account_id, instrument)
                    prices = result.get("prices", [])
                    for price in prices:
                        yield self._normalize_price(price, instrument)
                        self._event_count += 1
                        if self.max_events > 0 and self._event_count >= self.max_events:
                            break
                else:
                    # Mock mode: yield synthetic tick
                    yield self._synthetic_tick(instrument)
                    self._event_count += 1
            except TransportError as e:
                yield {
                    "event_type": "error",
                    "error": str(e),
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "oanda_practice",
                }
            if self._running:
                time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False

    def _normalize_price(self, price: Dict[str, Any], instrument: str) -> Dict[str, Any]:
        bid = float(price.get("bids", [{}])[0].get("price", 0)) if price.get("bids") else 0
        ask = float(price.get("asks", [{}])[0].get("price", 0)) if price.get("asks") else 0
        mid = (bid + ask) / 2 if bid and ask else 0
        spread = ask - bid if ask and bid else 0
        ts = price.get("time", datetime.now(timezone.utc).isoformat())
        return {
            "event_type": "tick",
            "symbol": instrument,
            "timestamp_utc": ts,
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread": spread,
            "volume": 0,
            "source": "oanda_practice",
        }

    def _synthetic_tick(self, instrument: str) -> Dict[str, Any]:
        return {
            "event_type": "tick",
            "symbol": instrument,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bid": 1.10000,
            "ask": 1.10005,
            "mid": 1.100025,
            "spread": 0.00005,
            "volume": 0,
            "source": "oanda_practice",
        }

    @property
    def event_count(self) -> int:
        return self._event_count
