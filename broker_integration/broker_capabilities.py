"""Broker capability definitions."""
from dataclasses import dataclass


@dataclass
class BrokerCapabilities:
    broker_name: str
    environment: str
    live_trading_enabled: bool = False
    supports_market_data: bool = False
    supports_paper_orders: bool = False
    supports_live_orders: bool = False
    supports_account_snapshot: bool = False
    supports_rest_api: bool = False
    supports_streaming_api: bool = False
    supports_fix_api: bool = False
    supports_mt4: bool = False
    supports_mt5: bool = False
