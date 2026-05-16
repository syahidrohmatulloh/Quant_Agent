"""OANDA instrument symbol utilities."""
from typing import Dict, Set

# Common symbol mappings: compact -> OANDA format
SYMBOL_MAP: Dict[str, str] = {
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
    "AUDUSD": "AUD_USD",
    "USDCAD": "USD_CAD",
    "USDCHF": "USD_CHF",
    "NZDUSD": "NZD_USD",
    "XAUUSD": "XAU_USD",
    "XAGUSD": "XAG_USD",
}


def to_oanda_symbol(symbol: str) -> str:
    """Convert compact symbol to OANDA format."""
    upper = symbol.upper().replace("_", "").replace("-", "")
    if upper in SYMBOL_MAP:
        return SYMBOL_MAP[upper]
    # Already in OANDA format?
    if "_" in symbol:
        return symbol.upper()
    return symbol.upper()


def from_oanda_symbol(oanda_symbol: str) -> str:
    """Convert OANDA format to compact symbol."""
    return oanda_symbol.replace("_", "")


def is_valid_oanda_symbol(symbol: str) -> bool:
    """Basic validation for OANDA instrument format."""
    return "_" in symbol and len(symbol.split("_")) == 2
