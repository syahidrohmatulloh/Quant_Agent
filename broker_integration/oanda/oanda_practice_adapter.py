"""OANDA practice broker adapter."""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..base import BaseBrokerAdapter
from ..broker_config import BrokerConfig
from ..broker_health import healthy, unhealthy
from ..broker_errors import MissingCredentialsError, DependencyMissingError


class OandaPracticeAdapter(BaseBrokerAdapter):
    """OANDA practice adapter with mock transport support."""

    def __init__(self, config: BrokerConfig, transport=None):
        super().__init__(config)
        self._transport = transport
        self._connected = False

    @property
    def broker_name(self) -> str:
        return "oanda"

    @property
    def environment(self) -> str:
        return "practice"

    def health_check(self) -> Dict[str, Any]:
        if not self.config.api_key:
            return unhealthy("missing_credentials", "OANDA_API_KEY env var not set")
        if self._transport is None:
            try:
                import requests
            except ImportError:
                return unhealthy("dependency_missing", "requests package not available")
        return healthy("ok", "OANDA practice adapter ready")

    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.config.api_key:
            return None
        account_id = self.config.account_id or "demo-account"
        masked = self._mask_account_id(account_id)
        return {
            "broker": "oanda",
            "environment": "practice",
            "account_id_masked": masked,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "currency": "USD",
            "cash": 100000.0,
            "equity": 100250.0,
            "margin_used": 0.0,
            "open_positions": [],
            "open_orders": [],
            "source": "broker_paper",
        }

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if self._transport:
            return self._transport.get_latest_tick(symbol)
        return self._normalize_tick(symbol, {
            "instrument": symbol,
            "time": datetime.now(timezone.utc).isoformat(),
            "bid": 1.10000,
            "ask": 1.10005,
        })

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        return []

    def submit_paper_order(self, symbol: str, direction: str, volume: float, price: float) -> Dict[str, Any]:
        return {
            "executed": True,
            "destination": "paper",
            "broker": self.broker_name,
            "environment": self.environment,
            "symbol": symbol,
            "direction": direction,
            "volume": volume,
            "price": price,
            "order_id": "oanda-paper-001",
        }

    def _normalize_tick(self, symbol: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        bid = float(raw.get("bid", 0))
        ask = float(raw.get("ask", 0))
        mid = (bid + ask) / 2 if bid and ask else 0
        spread = ask - bid if ask and bid else 0
        return {
            "symbol": symbol,
            "timestamp_utc": raw.get("time", datetime.now(timezone.utc).isoformat()),
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread": spread,
            "volume": 0,
            "source": "oanda_practice",
        }

    def _mask_account_id(self, account_id: str) -> str:
        if len(account_id) <= 4:
            return "****"
        return "****" + account_id[-4:]
