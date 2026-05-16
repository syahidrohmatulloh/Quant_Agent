"""Regional broker catalog."""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class RegionalBrokerCandidate:
    broker_id: str
    display_name: str
    category: str = "regional"
    regulator: str = ""
    regulator_country: str = ""
    legal_check_url: str = ""
    supports_indonesian_residents: str = "unknown_or_verify"
    account_opening_difficulty: str = "unknown"
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


REGIONAL_BROKERS: List[RegionalBrokerCandidate] = [
    RegionalBrokerCandidate(
        broker_id="ibkr",
        display_name="Interactive Brokers",
        category="global",
        regulator="SEC/CFTC/FCA/etc",
        regulator_country="US/UK/etc",
        legal_check_url="https://www.interactivebrokers.com/",
        supports_indonesian_residents="unknown_or_verify",
        account_opening_difficulty="medium",
        supports_demo_account="true",
        supports_api="true",
        supports_rest_api="true",
        supports_paper_orders="true",
        supports_market_data="true",
        supports_account_snapshot="true",
        integration_status="api_possible",
        notes="Established API. Paper trading available. Verify Indonesia eligibility.",
    ),
    RegionalBrokerCandidate(
        broker_id="oanda_sg",
        display_name="OANDA Singapore",
        category="regional",
        regulator="MAS",
        regulator_country="Singapore",
        legal_check_url="https://www.oanda.com/sg/",
        supports_indonesian_residents="unknown_or_verify",
        account_opening_difficulty="medium",
        supports_demo_account="true",
        supports_api="verify",
        supports_mt4="true",
        supports_mt5="true",
        supports_paper_orders="true",
        supports_market_data="true",
        integration_status="api_possible",
        notes="Demo and MT4/MT5 available. API access may vary by region.",
    ),
    RegionalBrokerCandidate(
        broker_id="alpaca",
        display_name="Alpaca",
        category="global",
        regulator="SEC/Finra",
        regulator_country="US",
        legal_check_url="https://alpaca.markets/",
        supports_indonesian_residents="unknown_or_verify",
        account_opening_difficulty="easy",
        supports_demo_account="true",
        supports_api="true",
        supports_rest_api="true",
        supports_paper_orders="true",
        supports_market_data="true",
        integration_status="api_possible",
        notes="API-first platform. Paper trading available. Verify Indonesia eligibility.",
    ),
    RegionalBrokerCandidate(
        broker_id="saxo",
        display_name="Saxo Bank",
        category="global",
        regulator="FCA/Danish FSA/etc",
        regulator_country="Denmark/UK/etc",
        legal_check_url="https://www.home.saxo/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_api="verify",
        integration_status="api_possible",
        notes="Demo available. API access may require partnership.",
    ),
    RegionalBrokerCandidate(
        broker_id="ig",
        display_name="IG",
        category="global",
        regulator="FCA/ASIC/etc",
        regulator_country="UK/Australia/etc",
        legal_check_url="https://www.ig.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_api="verify",
        integration_status="api_possible",
        notes="Demo available. API access may be limited.",
    ),
    RegionalBrokerCandidate(
        broker_id="cmc",
        display_name="CMC Markets",
        category="global",
        regulator="FCA/ASIC/etc",
        regulator_country="UK/Australia/etc",
        legal_check_url="https://www.cmcmarkets.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_api="verify",
        integration_status="api_possible",
        notes="Demo available. API access may be limited.",
    ),
    RegionalBrokerCandidate(
        broker_id="pepperstone",
        display_name="Pepperstone",
        category="global",
        regulator="ASIC/FCA/etc",
        regulator_country="Australia/UK/etc",
        legal_check_url="https://www.pepperstone.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_api="verify",
        supports_mt4="true",
        supports_mt5="true",
        integration_status="mt5_demo_possible",
        notes="MT4/MT5 demo available. API access may be limited.",
    ),
    RegionalBrokerCandidate(
        broker_id="fxcm",
        display_name="FXCM",
        category="global",
        regulator="FCA/ASIC/etc",
        regulator_country="UK/Australia/etc",
        legal_check_url="https://www.fxcm.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_api="verify",
        supports_mt4="true",
        integration_status="mt5_demo_possible",
        notes="Demo available. API access may be limited.",
    ),
    RegionalBrokerCandidate(
        broker_id="exness",
        display_name="Exness",
        category="global",
        regulator="FCA/CySEC/etc",
        regulator_country="UK/Cyprus/etc",
        legal_check_url="https://www.exness.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_mt4="true",
        supports_mt5="true",
        integration_status="mt5_demo_possible",
        notes="MT4/MT5 demo available. No public REST API documented.",
    ),
    RegionalBrokerCandidate(
        broker_id="xm",
        display_name="XM",
        category="global",
        regulator="CySEC/ASIC/etc",
        regulator_country="Cyprus/Australia/etc",
        legal_check_url="https://www.xm.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_mt4="true",
        supports_mt5="true",
        integration_status="mt5_demo_possible",
        notes="MT4/MT5 demo available. No public REST API documented.",
    ),
    RegionalBrokerCandidate(
        broker_id="fbs",
        display_name="FBS",
        category="global",
        regulator="IFC/CySEC/etc",
        regulator_country="Belize/Cyprus/etc",
        legal_check_url="https://fbs.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_mt4="true",
        supports_mt5="true",
        integration_status="mt5_demo_possible",
        notes="MT4/MT5 demo available. No public REST API documented.",
    ),
    RegionalBrokerCandidate(
        broker_id="tickmill",
        display_name="Tickmill",
        category="global",
        regulator="FCA/CySEC/etc",
        regulator_country="UK/Cyprus/etc",
        legal_check_url="https://www.tickmill.com/",
        supports_indonesian_residents="unknown_or_verify",
        supports_demo_account="true",
        supports_mt4="true",
        supports_mt5="true",
        integration_status="mt5_demo_possible",
        notes="MT4/MT5 demo available. No public REST API documented.",
    ),
]


def get_regional_broker(broker_id: str) -> RegionalBrokerCandidate:
    for b in REGIONAL_BROKERS:
        if b.broker_id == broker_id:
            return b
    return RegionalBrokerCandidate(
        broker_id=broker_id,
        display_name=broker_id,
        integration_status="unsupported",
        notes="Broker not in regional catalog.",
    )


def list_regional_brokers() -> List[Dict[str, Any]]:
    return [b.__dict__ for b in REGIONAL_BROKERS]
