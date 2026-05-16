"""OANDA account snapshot utilities."""
from typing import Dict, Any
from datetime import datetime, timezone


def build_oanda_snapshot(account_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    masked = "****" + account_id[-4:] if len(account_id) > 4 else "****"
    return {
        "broker": "oanda",
        "environment": "practice",
        "account_id_masked": masked,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "currency": raw.get("currency", "USD"),
        "cash": float(raw.get("balance", 100000)),
        "equity": float(raw.get("balance", 100000)) + float(raw.get("unrealizedPL", 0)),
        "margin_used": float(raw.get("marginUsed", 0)),
        "open_positions": raw.get("positions", []),
        "open_orders": raw.get("orders", []),
        "source": "broker_paper",
    }
