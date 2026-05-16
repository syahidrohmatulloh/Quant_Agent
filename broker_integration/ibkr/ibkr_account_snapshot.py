"""IBKR account snapshot utilities."""
from typing import Dict, Any
from datetime import datetime, timezone


def build_ibkr_snapshot(account_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    masked = "****" + account_id[-4:] if len(account_id) > 4 else "****"
    return {
        "broker": "ibkr",
        "environment": "paper",
        "account_id_masked": masked,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "currency": "USD",
        "cash": float(raw.get("cash", 100000)),
        "equity": float(raw.get("equity", 100000)),
        "margin_used": float(raw.get("margin_used", 0)),
        "open_positions": raw.get("positions", []),
        "open_orders": raw.get("orders", []),
        "source": "broker_paper",
    }
