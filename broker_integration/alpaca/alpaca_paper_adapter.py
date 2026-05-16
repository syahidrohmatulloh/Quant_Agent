"""Alpaca paper broker adapter."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..base import BaseBrokerAdapter
from ..broker_config import BrokerConfig
from ..broker_health import healthy, unhealthy


class AlpacaPaperAdapter(BaseBrokerAdapter):
    """Alpaca paper trading adapter."""

    def __init__(self, config: BrokerConfig, transport=None):
        super().__init__(config)
        self._transport = transport

    @property
    def broker_name(self) -> str:
        return "alpaca"

    @property
    def environment(self) -> str:
        return "paper"

    def health_check(self) -> Dict[str, Any]:
        if not self.config.api_key:
            return unhealthy("missing_credentials", "ALPACA_API_KEY env var not set")
        if self._transport is None:
            try:
                import requests
            except ImportError:
                return unhealthy("dependency_missing", "requests package not available")
        return healthy("ok", "Alpaca paper adapter ready")

    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.config.api_key:
            return None
        account_id = self.config.account_id or "paper-account"
        masked = self._mask_account_id(account_id)
        return {
            "broker": "alpaca",
            "environment": "paper",
            "account_id_masked": masked,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "currency": "USD",
            "cash": 100000.0,
            "equity": 100000.0,
            "margin_used": 0.0,
            "open_positions": [],
            "open_orders": [],
            "source": "broker_paper",
        }

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if self._transport:
            return self._transport.get_latest_tick(symbol)
        return {
            "symbol": symbol,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bid": 150.00,
            "ask": 150.01,
            "mid": 150.005,
            "spread": 0.01,
            "volume": 1000,
            "source": "alpaca_paper",
        }

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
            "order_id": "alpaca-paper-001",
        }

    def _mask_account_id(self, account_id: str) -> str:
        if len(account_id) <= 4:
            return "****"
        return "****" + account_id[-4:]

    def health_check(self):
        import os
        key_name = getattr(self.config, "api_key_env", None)
        key = os.getenv(key_name) if key_name else None
        if not key:
            return {
                "broker": getattr(self.config, "broker_name", "unknown"),
                "environment": getattr(self.config, "environment", "paper"),
                "healthy": False,
                "reason": "missing_credentials",
                "paper_only": True,
            }
        return {
            "broker": getattr(self.config, "broker_name", "unknown"),
            "environment": getattr(self.config, "environment", "paper"),
            "healthy": True,
            "reason": "ok",
            "paper_only": True,
        }

