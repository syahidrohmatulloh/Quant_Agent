"""Broker reconciliation engine."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class BrokerReconciliation:
    def __init__(self, max_age_seconds: float = 300.0):
        self.max_age_seconds = max_age_seconds

    def reconcile(self, internal: Dict[str, Any], broker: Dict[str, Any]) -> Dict[str, Any]:
        mismatches: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        # Stale snapshot check
        broker_ts = broker.get("timestamp_utc", "")
        if broker_ts:
            try:
                bt = datetime.fromisoformat(broker_ts.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                age = (now - bt).total_seconds()
                if age > self.max_age_seconds:
                    warnings.append({"field": "stale_snapshot", "age_seconds": age})
            except Exception:
                warnings.append({"field": "timestamp_parse_error"})

        # Currency mismatch
        if internal.get("currency") and broker.get("currency"):
            if internal["currency"] != broker["currency"]:
                mismatches.append({"field": "currency", "internal": internal["currency"], "broker": broker["currency"]})

        # Cash/equity mismatch
        if internal.get("cash") != broker.get("cash"):
            mismatches.append({"field": "cash", "internal": internal.get("cash"), "broker": broker.get("cash")})
        if internal.get("equity") != broker.get("equity"):
            mismatches.append({"field": "equity", "internal": internal.get("equity"), "broker": broker.get("equity")})

        # Position mismatch
        internal_positions = {p.get("symbol", ""): p for p in internal.get("open_positions", [])}
        broker_positions = {p.get("symbol", p.get("instrument", "")): p for p in broker.get("open_positions", [])}

        for sym, pos in internal_positions.items():
            if sym not in broker_positions:
                mismatches.append({"field": "missing_broker_position", "symbol": sym})
            else:
                bpos = broker_positions[sym]
                if pos.get("volume") != bpos.get("volume"):
                    mismatches.append({"field": "quantity_mismatch", "symbol": sym, "internal": pos.get("volume"), "broker": bpos.get("volume")})
                if pos.get("entry_price") != bpos.get("entry_price"):
                    mismatches.append({"field": "avg_price_mismatch", "symbol": sym, "internal": pos.get("entry_price"), "broker": bpos.get("entry_price")})

        for sym in broker_positions:
            if sym not in internal_positions:
                mismatches.append({"field": "extra_broker_position", "symbol": sym})

        # Order mismatch
        internal_orders = {o.get("order_id", ""): o for o in internal.get("open_orders", [])}
        broker_orders = {o.get("order_id", ""): o for o in broker.get("open_orders", [])}

        for oid in internal_orders:
            if oid not in broker_orders:
                mismatches.append({"field": "missing_broker_order", "order_id": oid})

        for oid in broker_orders:
            if oid not in internal_orders:
                mismatches.append({"field": "extra_broker_order", "order_id": oid})

        status = "matched" if not mismatches else "mismatch"
        if warnings and status == "matched":
            status = "warning"

        return {
            "status": status,
            "mismatches": mismatches,
            "warnings": warnings,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

    def is_severe(self, result: Dict[str, Any]) -> bool:
        severe_fields = {"missing_broker_position", "extra_broker_position", "quantity_mismatch", "cash"}
        for m in result.get("mismatches", []):
            if m.get("field") in severe_fields:
                return True
        return False
