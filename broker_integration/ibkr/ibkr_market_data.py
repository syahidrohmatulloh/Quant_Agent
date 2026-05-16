"""IBKR market data normalization."""
from typing import Dict, Any
from datetime import datetime, timezone


def normalize_ibkr_tick(symbol: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    bid = float(raw.get("bid", 0))
    ask = float(raw.get("ask", 0))
    mid = (bid + ask) / 2 if bid and ask else 0
    spread = ask - bid if ask and bid else 0
    ts = raw.get("time", datetime.now(timezone.utc).isoformat())
    return {
        "symbol": symbol,
        "timestamp_utc": ts,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread": spread,
        "volume": int(raw.get("volume", 0)),
        "source": "ibkr_paper",
    }
