
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class DataNormalizer:
    @staticmethod
    def normalize_tick(raw: Dict[str, Any], source: str = "unknown") -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        bid = raw.get("bid") or raw.get("Bid") or raw.get("BID")
        ask = raw.get("ask") or raw.get("Ask") or raw.get("ASK")
        if bid is None or ask is None:
            return None
        try:
            bid_f = float(bid)
            ask_f = float(ask)
        except (ValueError, TypeError):
            return None
        if bid_f <= 0 or ask_f <= 0 or ask_f < bid_f:
            return None
        ts = raw.get("timestamp") or raw.get("time") or datetime.now(timezone.utc).isoformat()
        return {
            "symbol": str(raw.get("symbol", raw.get("Symbol", "UNKNOWN"))),
            "timestamp_utc": str(ts),
            "bid": round(bid_f, 5),
            "ask": round(ask_f, 5),
            "mid": round((bid_f + ask_f) / 2, 5),
            "close": round((bid_f + ask_f) / 2, 5),
            "spread": round(ask_f - bid_f, 5),
            "volume": float(raw.get("volume", 0)) if raw.get("volume") is not None else 0.0,
            "source": source
        }

    @staticmethod
    def normalize_bar(raw: Dict[str, Any], source: str = "unknown") -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        required = ["open", "high", "low", "close"]
        for key in required:
            if key not in raw and key.capitalize() not in raw:
                return None
        try:
            o = float(raw.get("open", raw.get("Open")))
            h = float(raw.get("high", raw.get("High")))
            l = float(raw.get("low", raw.get("Low")))
            c = float(raw.get("close", raw.get("Close")))
        except (ValueError, TypeError):
            return None
        if not (h >= l and h >= c and l <= c and o > 0):
            return None
        ts = raw.get("timestamp") or raw.get("time") or datetime.now(timezone.utc).isoformat()
        return {
            "timestamp_utc": str(ts),
            "symbol": str(raw.get("symbol", raw.get("Symbol", "UNKNOWN"))),
            "open": round(o, 5),
            "high": round(h, 5),
            "low": round(l, 5),
            "close": round(c, 5),
            "volume": float(raw.get("volume", 0)) if raw.get("volume") is not None else 0.0,
            "source": source
        }
