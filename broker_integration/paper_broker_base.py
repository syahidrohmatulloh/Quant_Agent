"""Paper broker adapter base with safety gates."""
from typing import Dict, Any, Optional, List
from .base import BaseBrokerAdapter
from .broker_config import BrokerConfig
from .broker_health import healthy, unhealthy


class PaperBrokerAdapter(BaseBrokerAdapter):
    """Base for paper/demo broker adapters."""

    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        if not config.paper_only:
            raise ValueError("PaperBrokerAdapter requires paper_only=True")

    @property
    def live_trading_enabled(self) -> bool:
        return False

    @property
    def supports_live_orders(self) -> bool:
        return False

    def health_check(self) -> Dict[str, Any]:
        if not self.config.api_key:
            return unhealthy("missing_credentials", "API key not found in environment")
        return healthy()

    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        return None

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        return None

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        return []

    def submit_paper_order(self, symbol: str, direction: str, volume: float, price: float) -> Dict[str, Any]:
        return {
            "executed": False,
            "reason": "Paper order submission not implemented in base",
            "broker": self.broker_name,
            "environment": self.environment,
        }
