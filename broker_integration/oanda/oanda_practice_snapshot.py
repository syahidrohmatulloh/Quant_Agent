"""OANDA practice account snapshot with real transport support."""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from broker_integration.broker_config import BrokerConfig
from broker_integration.transport.redaction import mask_account_id
from .oanda_http_transport import OandaHttpTransport
from .oanda_practice_positions import parse_positions


class OandaPracticeSnapshot:
    """Fetch and parse OANDA practice account snapshot."""

    def __init__(self, config: BrokerConfig, transport: Optional[OandaHttpTransport] = None):
        self.config = config
        self.transport = transport

    def fetch(self) -> Optional[Dict[str, Any]]:
        if not self.config.api_key:
            return None
        if self.transport is None:
            return None
        account_id = self.config.account_id
        if not account_id:
            return None
        try:
            summary = self.transport.get_account(account_id)
            positions_raw = self.transport.get_positions(account_id)
            orders_raw = self.transport.get_orders(account_id)
            account = summary.get("account", {})
            return self._build_snapshot(account, positions_raw, orders_raw)
        except Exception:
            return None

    def _build_snapshot(self, account: Dict[str, Any], positions_raw: Dict[str, Any], orders_raw: Dict[str, Any]) -> Dict[str, Any]:
        account_id = account.get("id", "unknown")
        masked = mask_account_id(account_id)
        positions = parse_positions(positions_raw)
        orders = []
        for o in orders_raw.get("orders", []):
            orders.append({
                "order_id": o.get("id", ""),
                "instrument": o.get("instrument", ""),
                "units": o.get("units", ""),
                "type": o.get("type", ""),
            })
        return {
            "broker": "oanda",
            "environment": "practice",
            "account_id_masked": masked,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "currency": account.get("currency", "USD"),
            "cash": float(account.get("balance", 0)),
            "equity": float(account.get("NAV", 0)),
            "margin_used": float(account.get("marginUsed", 0)),
            "open_positions": positions,
            "open_orders": orders,
            "source": "broker_paper",
        }
