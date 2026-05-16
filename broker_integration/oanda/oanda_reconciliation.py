"""OANDA reconciliation logic."""
from typing import Dict, Any, List
from datetime import datetime, timezone


def reconcile_oanda(internal: Dict[str, Any], broker: Dict[str, Any]) -> Dict[str, Any]:
    mismatches: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    if internal.get("cash") != broker.get("cash"):
        mismatches.append({"field": "cash", "internal": internal.get("cash"), "broker": broker.get("cash")})

    if internal.get("equity") != broker.get("equity"):
        mismatches.append({"field": "equity", "internal": internal.get("equity"), "broker": broker.get("equity")})

    internal_positions = {p["symbol"]: p for p in internal.get("open_positions", [])}
    broker_positions = {p.get("instrument", p.get("symbol", "")): p for p in broker.get("open_positions", [])}

    for sym, pos in internal_positions.items():
        if sym not in broker_positions:
            mismatches.append({"field": "missing_broker_position", "symbol": sym})

    for sym, pos in broker_positions.items():
        if sym not in internal_positions:
            mismatches.append({"field": "extra_broker_position", "symbol": sym})

    status = "matched" if not mismatches else "mismatch"
    return {
        "status": status,
        "mismatches": mismatches,
        "warnings": warnings,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
