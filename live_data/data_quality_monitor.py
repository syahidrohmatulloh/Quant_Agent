
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

class DataQualityMonitor:
    def __init__(self, max_stale_seconds: float = 30.0,
                 max_spread_multiplier: float = 5.0,
                 max_missing_bars: int = 3):
        self.max_stale_seconds = max_stale_seconds
        self.max_spread_multiplier = max_spread_multiplier
        self.max_missing_bars = max_missing_bars
        self._last_tick: Dict[str, Dict[str, Any]] = {}
        self._last_bar_count: Dict[str, int] = {}
        self._baseline_spread: Dict[str, float] = {}

    def check_tick(self, tick: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        symbol = tick.get("symbol", "UNKNOWN")
        now = datetime.now(timezone.utc)
        # Stale data
        try:
            ts = datetime.fromisoformat(tick["timestamp_utc"].replace("Z", "+00:00"))
            if (now - ts).total_seconds() > self.max_stale_seconds:
                issues.append({"type": "stale", "symbol": symbol, "seconds": (now - ts).total_seconds()})
        except Exception:
            issues.append({"type": "bad_timestamp", "symbol": symbol})
        # Missing bid/ask
        if tick.get("bid") is None or tick.get("ask") is None:
            issues.append({"type": "missing_bid_ask", "symbol": symbol})
        # Negative/zero price
        if (tick.get("bid", 1) <= 0) or (tick.get("ask", 1) <= 0):
            issues.append({"type": "invalid_price", "symbol": symbol})
        # Spread widening
        spread = tick.get("spread", 0)
        if symbol in self._baseline_spread and self._baseline_spread[symbol] > 0:
            if spread > self._baseline_spread[symbol] * self.max_spread_multiplier:
                issues.append({"type": "wide_spread", "symbol": symbol, "spread": spread})
        else:
            self._baseline_spread[symbol] = spread if spread > 0 else 1e-6
        # Timestamp backwards
        if symbol in self._last_tick:
            last_ts_str = self._last_tick[symbol].get("timestamp_utc")
            try:
                last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
                if ts < last_ts:
                    issues.append({"type": "backwards_timestamp", "symbol": symbol})
            except Exception:
                pass
        self._last_tick[symbol] = tick
        return issues

    def check_bars(self, symbol: str, bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        issues = []
        if not bars:
            issues.append({"type": "missing_bars", "symbol": symbol})
            return issues
        # Duplicate timestamps
        timestamps = [b.get("timestamp_utc") for b in bars]
        if len(timestamps) != len(set(timestamps)):
            issues.append({"type": "duplicate_bars", "symbol": symbol})
        # Excessive missing bars
        prev = self._last_bar_count.get(symbol, 0)
        gap = abs(len(bars) - prev)
        if gap > self.max_missing_bars:
            issues.append({"type": "excessive_missing_bars", "symbol": symbol, "gap": gap})
        self._last_bar_count[symbol] = len(bars)
        return issues

    def is_healthy(self, tick: Dict[str, Any]) -> bool:
        return len(self.check_tick(tick)) == 0
