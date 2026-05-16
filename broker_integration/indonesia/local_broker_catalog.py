"""Local Indonesian broker catalog."""
from typing import Dict, Any, List
from dataclasses import dataclass, field
from .bappebti_registry import get_bappebti_info


@dataclass
class LocalBrokerCandidate:
    broker_id: str
    display_name: str
    regulator: str = "BAPPEBTI"
    regulator_country: str = "Indonesia"
    legal_check_url: str = "https://www.bappebti.go.id/"
    supports_indonesian_residents: bool = True
    account_opening_difficulty: str = "medium"
    supports_demo_account: str = "unknown"
    supports_api: str = "unknown"
    supports_mt4: str = "unknown"
    supports_mt5: str = "unknown"
    supports_rest_api: str = "unknown"
    supports_streaming_api: str = "unknown"
    supports_fix_api: str = "unknown"
    supports_paper_orders: str = "unknown"
    supports_market_data: str = "unknown"
    supports_account_snapshot: str = "unknown"
    live_trading_enabled: bool = False
    integration_status: str = "mock_only"
    notes: str = ""
    last_verified_date: str = ""


LOCAL_BROKERS: List[LocalBrokerCandidate] = [
    LocalBrokerCandidate(
        broker_id="mifx",
        display_name="MIFX / Monex Investindo Futures",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Established local broker. MT5 demo may be available.",
    ),
    LocalBrokerCandidate(
        broker_id="gkinvest",
        display_name="GKInvest / Global Kapital Investama Berjangka",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Local broker with MT4/MT5 platform.",
    ),
    LocalBrokerCandidate(
        broker_id="hsb",
        display_name="HSB Investasi",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Popular local broker. Verify demo account availability.",
    ),
    LocalBrokerCandidate(
        broker_id="finex",
        display_name="Finex",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Local broker. Check MT5 demo availability.",
    ),
    LocalBrokerCandidate(
        broker_id="dupoin",
        display_name="Dupoin Futures",
        supports_demo_account="unknown",
        supports_api="unknown",
        supports_mt4="unknown",
        supports_mt5="unknown",
        integration_status="mock_only",
        notes="Limited public information on API/demo.",
    ),
    LocalBrokerCandidate(
        broker_id="maxco",
        display_name="Maxco Futures",
        supports_demo_account="unknown",
        supports_api="unknown",
        supports_mt4="unknown",
        supports_mt5="unknown",
        integration_status="mock_only",
        notes="Limited public information on API/demo.",
    ),
    LocalBrokerCandidate(
        broker_id="octa_id",
        display_name="Octa Investama Berjangka",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Verify demo and MT5 availability.",
    ),
    LocalBrokerCandidate(
        broker_id="xtb_id",
        display_name="XTB Indonesia Berjangka",
        supports_demo_account="verify",
        supports_api="unknown",
        supports_mt4="verify",
        supports_mt5="verify",
        integration_status="mt5_demo_possible_or_mock_only",
        notes="Local entity of global XTB brand.",
    ),
]


def get_local_broker(broker_id: str) -> LocalBrokerCandidate:
    for b in LOCAL_BROKERS:
        if b.broker_id == broker_id:
            return b
    return LocalBrokerCandidate(
        broker_id=broker_id,
        display_name=broker_id,
        integration_status="unsupported",
        notes="Broker not in local catalog.",
    )


def list_local_brokers() -> List[Dict[str, Any]]:
    return [b.__dict__ for b in LOCAL_BROKERS]
