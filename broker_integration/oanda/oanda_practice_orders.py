"""OANDA practice order client — paper-only, default disabled."""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from broker_integration.broker_config import BrokerConfig
from broker_integration.transport.network_errors import LiveTradingDisabledError
from .oanda_http_transport import OandaHttpTransport
from .oanda_instruments import to_oanda_symbol


class OandaPracticeOrderClient:
    """OANDA practice order submission — strictly paper-only."""

    def __init__(self, config: BrokerConfig, transport: Optional[OandaHttpTransport] = None):
        self.config = config
        self.transport = transport

    def submit_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        units: float,
        order_type: str = "MARKET",
        dry_run: bool = True,
        model_id: str = "",
        signal_id: str = "",
    ) -> Dict[str, Any]:
        # Safety gate 1: default disabled
        if not self.config.allow_order_submission:
            return {
                "executed": False,
                "reason": "order_submission_disabled",
                "broker": "oanda",
                "environment": self.config.environment,
                "paper_only": True,
                "dry_run": dry_run,
            }

        # Safety gate 2: live orders rejected
        if self.config.allow_live_orders:
            raise LiveTradingDisabledError("allow_live_orders is True. System is paper-only.")

        # Safety gate 3: environment must be practice
        if self.config.environment.lower() not in ("practice", "paper", "demo"):
            raise LiveTradingDisabledError(f"Environment '{self.config.environment}' is not practice.")

        # Safety gate 4: paper_only must be true
        if not self.config.paper_only:
            raise LiveTradingDisabledError("paper_only must be True for OANDA practice.")

        instrument = to_oanda_symbol(symbol)
        order_payload = {
            "order": {
                "type": order_type,
                "instrument": instrument,
                "units": str(units) if side.lower() == "buy" else str(-units),
                "timeInForce": "FOK",
            },
            "dry_run": dry_run,
            "model_id": model_id,
            "signal_id": signal_id,
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        if dry_run:
            return {
                "executed": False,
                "reason": "dry_run",
                "broker": "oanda",
                "environment": self.config.environment,
                "paper_only": True,
                "payload": order_payload,
                "audit": {
                    "event": "dry_run_order",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "model_id": model_id,
                    "signal_id": signal_id,
                },
            }

        # Only reach here if dry_run=False AND allow_order_submission=True
        if self.transport is None:
            return {
                "executed": False,
                "reason": "no_transport",
                "broker": "oanda",
                "environment": self.config.environment,
            }

        account_id = self.config.account_id
        if not account_id:
            return {
                "executed": False,
                "reason": "missing_account_id",
                "broker": "oanda",
                "environment": self.config.environment,
            }

        try:
            result = self.transport.post_order(account_id, order_payload)
            return {
                "executed": True,
                "reason": "submitted_to_practice",
                "broker": "oanda",
                "environment": self.config.environment,
                "paper_only": True,
                "order_id": result.get("orderFillTransaction", {}).get("id", "unknown"),
                "audit": {
                    "event": "practice_order_submitted",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "model_id": model_id,
                    "signal_id": signal_id,
                },
            }
        except Exception as e:
            return {
                "executed": False,
                "reason": f"submission_error: {e}",
                "broker": "oanda",
                "environment": self.config.environment,
                "paper_only": True,
            }
