"""MT5 demo adapter for Indonesian brokers.

Optional dependency on MetaTrader5 package.
Read-only market data only.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..base import BaseBrokerAdapter
from ..broker_config import BrokerConfig
from ..broker_health import healthy, unhealthy


class MT5DemoAdapter(BaseBrokerAdapter):
    """MT5 demo adapter. Read-only. No order submission."""

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self._mt5 = None

    @property
    def broker_name(self) -> str:
        return self.config.broker_name

    @property
    def environment(self) -> str:
        return "demo"

    def health_check(self) -> Dict[str, Any]:
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
            if not mt5.initialize():
                return unhealthy("mt5_init_failed", "MetaTrader5 initialization failed")
            return healthy("ok", "MT5 demo connected")
        except ImportError:
            return unhealthy("dependency_missing", "MetaTrader5 package not available")

    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        if self._mt5 is None:
            return None
        account = self._mt5.account_info()
        if account is None:
            return None
        account_id = str(account.login)
        masked = "****" + account_id[-4:] if len(account_id) > 4 else "****"
        return {
            "broker": self.broker_name,
            "environment": "demo",
            "account_id_masked": masked,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "currency": account.currency,
            "cash": float(account.balance),
            "equity": float(account.equity),
            "margin_used": float(account.margin),
            "open_positions": [],
            "open_orders": [],
            "source": "mt5_demo",
        }

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        if self._mt5 is None:
            return None
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {
            "symbol": symbol,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bid": float(tick.bid),
            "ask": float(tick.ask),
            "mid": (float(tick.bid) + float(tick.ask)) / 2,
            "spread": float(tick.ask) - float(tick.bid),
            "volume": int(tick.volume),
            "source": f"{self.broker_name}_mt5_demo",
        }

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        return []

    def submit_paper_order(self, symbol: str, direction: str, volume: float, price: float) -> Dict[str, Any]:
        return {
            "executed": False,
            "reason": "MT5 demo adapter is read-only. No order submission.",
            "broker": self.broker_name,
            "environment": self.environment,
        }
