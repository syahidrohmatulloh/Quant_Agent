"""Base broker adapter interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class BaseBrokerAdapter(ABC):
    """Abstract base for all broker adapters."""

    def __init__(self, config: "BrokerConfig"):
        self.config = config

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return health status dict."""
        pass

    @abstractmethod
    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        """Return normalized account snapshot."""
        pass

    @abstractmethod
    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return normalized tick."""
        pass

    @abstractmethod
    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        """Return normalized bars."""
        pass

    @abstractmethod
    def submit_paper_order(self, symbol: str, direction: str, volume: float, price: float) -> Dict[str, Any]:
        """Submit a paper/demo order. Must never submit live orders."""
        pass

    @property
    @abstractmethod
    def broker_name(self) -> str:
        pass

    @property
    @abstractmethod
    def environment(self) -> str:
        pass

    @property
    def live_trading_enabled(self) -> bool:
        return False

    @property
    def supports_market_data(self) -> bool:
        return True

    @property
    def supports_paper_orders(self) -> bool:
        return True

    @property
    def supports_live_orders(self) -> bool:
        return False
