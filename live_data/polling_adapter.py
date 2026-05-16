
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from live_data.base_adapter import BaseMarketDataAdapter
from live_data.data_normalizer import DataNormalizer

class PollingAdapter(BaseMarketDataAdapter):
    def __init__(self, provider: Callable[[str], Optional[Dict[str, Any]]],
                 interval_seconds: float = 5.0,
                 timeout_seconds: float = 10.0,
                 max_retries: int = 3,
                 source: str = "polling"):
        self.provider = provider
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.source = source
        self._connected = False
        self._last_tick: Optional[Dict[str, Any]] = None
        self._failures = 0

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def _fetch_with_retry(self, symbol: str) -> Optional[Dict[str, Any]]:
        for attempt in range(self.max_retries):
            try:
                raw = self.provider(symbol)
                if raw:
                    self._failures = 0
                    return raw
            except Exception:
                pass
            if attempt < self.max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
        self._failures += 1
        return None

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._connected:
            return None
        raw = self._fetch_with_retry(symbol)
        if raw:
            tick = DataNormalizer.normalize_tick(raw, self.source)
            self._last_tick = tick
            return tick
        return self._last_tick

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        # Polling adapter does not maintain bar history
        tick = self.get_latest_tick(symbol)
        return [tick] if tick else []

    def health_check(self) -> Dict[str, Any]:
        return {
            "connected": self._connected,
            "failures": self._failures,
            "has_last_tick": self._last_tick is not None,
            "last_tick_timestamp": self._last_tick.get("timestamp_utc") if self._last_tick else None
        }
