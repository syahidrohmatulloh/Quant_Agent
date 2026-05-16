"""Broker configuration with paper-only safety gates."""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrokerConfig:
    broker_name: str
    environment: str  # "paper", "practice", "demo"
    api_key_env: str = ""
    api_secret_env: str = ""
    account_id_env: str = ""
    base_url: str = ""
    paper_only: bool = True
    allow_order_submission: bool = False
    allow_live_orders: bool = False
    market_data_enabled: bool = True
    account_snapshot_enabled: bool = True
    max_reconnect_attempts: int = 5
    request_timeout_seconds: int = 30

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        env_lower = self.environment.lower()
        if env_lower in ("live", "production", "real"):
            raise BrokerConfigError(
                f"Live environment '{self.environment}' is rejected. "
                "Only paper/practice/demo allowed."
            )
        if self.allow_live_orders:
            raise BrokerConfigError(
                "allow_live_orders=True is rejected. "
                "System is paper-only."
            )
        live_env = os.environ.get("LIVE_TRADING_ENABLED", "").lower()
        if live_env in ("true", "1", "yes"):
            raise BrokerConfigError(
                "LIVE_TRADING_ENABLED environment variable is set. "
                "Phase 8 tools fail closed."
            )

    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get(self.api_key_env) if self.api_key_env else None

    @property
    def api_secret(self) -> Optional[str]:
        return os.environ.get(self.api_secret_env) if self.api_secret_env else None

    @property
    def account_id(self) -> Optional[str]:
        return os.environ.get(self.account_id_env) if self.account_id_env else None

    def __repr__(self) -> str:
        return (
            f"BrokerConfig(broker_name={self.broker_name}, "
            f"environment={self.environment}, "
            f"paper_only={self.paper_only}, "
            f"allow_live_orders={self.allow_live_orders})"
        )


class BrokerConfigError(ValueError):
    pass
