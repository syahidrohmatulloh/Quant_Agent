"""Fbs regional adapter stub.

Integration status: mt5_demo_possible
No live trading. No real API calls.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ..base import BaseBrokerAdapter
from ..broker_config import BrokerConfig
from ..broker_health import healthy, unhealthy


class FbsAdapter(BaseBrokerAdapter):
    def __init__(self, config: BrokerConfig):
        super().__init__(config)

    @property
    def broker_name(self) -> str:
        return "fbs"

    @property
    def environment(self) -> str:
        return "demo"

    def health_check(self) -> Dict[str, Any]:
        return unhealthy("integration_status", "mt5_demo_possible")

    def get_account_snapshot(self) -> Optional[Dict[str, Any]]:
        return None

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        return None

    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int) -> List[Dict[str, Any]]:
        return []

    def submit_paper_order(self, symbol: str, direction: str, volume: float, price: float) -> Dict[str, Any]:
        return {
            "executed": False,
            "reason": "Fbs adapter is stub/mock only.",
            "broker": self.broker_name,
            "environment": self.environment,
        }
