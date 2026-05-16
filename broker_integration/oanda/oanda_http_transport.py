"""OANDA practice HTTP transport."""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from broker_integration.transport.http_transport import RequestsHttpTransport
from broker_integration.transport.auth import EnvAuth
from broker_integration.transport.retry_policy import RetryPolicy
from broker_integration.transport.rate_limit import RateLimiter
from broker_integration.transport.network_errors import TransportError, RateLimitError, UnauthorizedError
from broker_integration.broker_config import BrokerConfig
from .oanda_rate_limit import OandaRateLimiter
from .oanda_errors import OandaLiveEndpointError


class OandaHttpTransport(RequestsHttpTransport):
    """OANDA practice HTTP transport with safety gates."""

    def __init__(
        self,
        config: BrokerConfig,
        retry_policy: Optional[RetryPolicy] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self._validate_safety(config)
        auth = EnvAuth(
            api_key_env=config.api_key_env,
            api_secret_env=config.api_secret_env,
        )
        super().__init__(
            base_url=config.base_url,
            auth=auth,
            retry_policy=retry_policy or RetryPolicy(),
            rate_limiter=rate_limiter or OandaRateLimiter(),
            timeout_seconds=config.request_timeout_seconds,
        )
        self.config = config

    def _validate_safety(self, config: BrokerConfig) -> None:
        """Reject live endpoints."""
        url = config.base_url.lower()
        if "api-fxtrade" in url or "live" in url or "production" in url:
            raise OandaLiveEndpointError(
                f"OANDA base_url '{config.base_url}' appears to be a live endpoint. "
                "Only practice (api-fxpractice) allowed."
            )
        if config.environment.lower() not in ("practice", "paper", "demo"):
            raise OandaLiveEndpointError(
                f"OANDA environment '{config.environment}' is not practice/paper/demo."
            )

    def get_account(self, account_id: str) -> Dict[str, Any]:
        return self.get(f"/v3/accounts/{account_id}/summary")

    def get_positions(self, account_id: str) -> Dict[str, Any]:
        return self.get(f"/v3/accounts/{account_id}/positions")

    def get_orders(self, account_id: str) -> Dict[str, Any]:
        return self.get(f"/v3/accounts/{account_id}/orders")

    def get_latest_price(self, account_id: str, instrument: str) -> Dict[str, Any]:
        return self.get(f"/v3/accounts/{account_id}/pricing", params={"instruments": instrument})

    def get_candles(self, instrument: str, granularity: str = "M1", count: int = 10) -> Dict[str, Any]:
        return self.get(
            f"/v3/instruments/{instrument}/candles",
            params={"granularity": granularity, "count": count, "price": "M"},
        )

    def post_order(self, account_id: str, order: Dict[str, Any]) -> Dict[str, Any]:
        return self.post(f"/v3/accounts/{account_id}/orders", json_data=order)

    def health_check(self) -> Dict[str, Any]:
        if not self.config.api_key:
            return {
                "broker": "oanda",
                "environment": self.config.environment,
                "healthy": False,
                "reason": "missing_credentials",
                "paper_only": True,
            }
        try:
            # Lightweight check: list accounts
            result = self.get("/v3/accounts")
            return {
                "broker": "oanda",
                "environment": self.config.environment,
                "healthy": True,
                "reason": "ok",
                "paper_only": True,
                "accounts": len(result.get("accounts", [])),
            }
        except UnauthorizedError:
            return {
                "broker": "oanda",
                "environment": self.config.environment,
                "healthy": False,
                "reason": "unauthorized",
                "paper_only": True,
            }
        except RateLimitError:
            return {
                "broker": "oanda",
                "environment": self.config.environment,
                "healthy": False,
                "reason": "rate_limited",
                "paper_only": True,
            }
        except TransportError as e:
            return {
                "broker": "oanda",
                "environment": self.config.environment,
                "healthy": False,
                "reason": f"transport_error: {e}",
                "paper_only": True,
            }
