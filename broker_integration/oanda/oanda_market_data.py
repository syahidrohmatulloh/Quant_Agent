"""OANDA practice market data normalization."""
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def normalize_oanda_tick(symbol: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    bid = float(raw.get("bid", raw.get("bids", [{}])[0].get("price", 0)))
    ask = float(raw.get("ask", raw.get("asks", [{}])[0].get("price", 0)))
    mid = (bid + ask) / 2 if bid and ask else 0
    spread = ask - bid if ask and bid else 0
    ts = raw.get("time", datetime.now(timezone.utc).isoformat())
    return {
        "symbol": symbol,
        "timestamp_utc": ts,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread": round((spread), 10),
        "volume": 0,
        "source": "oanda_practice",
    }


def normalize_oanda_bar(symbol: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    ts = raw.get("time", datetime.now(timezone.utc).isoformat())
    return {
        "symbol": symbol,
        "timestamp_utc": ts,
        "open": float(raw.get("o", raw.get("open", 0))),
        "high": float(raw.get("h", raw.get("high", 0))),
        "low": float(raw.get("l", raw.get("low", 0))),
        "close": float(raw.get("c", raw.get("close", 0))),
        "volume": int(raw.get("volume", 0)),
        "source": "oanda_practice",
    }
