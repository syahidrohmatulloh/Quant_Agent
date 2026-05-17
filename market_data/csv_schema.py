"""
CSV schema definitions, column aliases, and filename inference.
Data-only. No live trading.
"""
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

TIMESTAMP_ALIASES: Set[str] = {"timestamp", "time", "date", "datetime"}
REQUIRED_PRICE_COLUMNS: Set[str] = {"open", "high", "low", "close"}
VOLUME_ALIASES: Set[str] = {"volume", "tick_volume", "tickvol", "vol"}
OPTIONAL_COLUMNS: Set[str] = {"spread", "real_volume", "symbol", "timeframe", "source"}

NORMALIZED_SCHEMA: Set[str] = {
    "timestamp", "open", "high", "low", "close", "volume", "tick_volume",
    "spread", "real_volume", "symbol", "timeframe", "source"
}

TIMESTAMP_FORMATS: List[str] = [
    "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y%m%d %H:%M:%S",
    "%Y%m%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
]


@dataclass
class InferredMetadata:
    symbol: str = "UNKNOWN"
    timeframe: str = "UNKNOWN"
    source: str = "UNKNOWN"


def infer_from_filename(filename: str) -> InferredMetadata:
    """
    Infer symbol/timeframe/source from filename patterns:
      mt5_EURUSD_H1.csv
      EURUSD_H1.csv
      oanda_EUR_USD_M15.csv
      GBPUSD_M5.csv
    """
    import re
    name = filename.lower().replace(".csv", "").replace(".jsonl", "")
    meta = InferredMetadata()

    # Source prefix
    if name.startswith("mt5_"):
        meta.source = "mt5"
        name = name[4:]
    elif name.startswith("oanda_"):
        meta.source = "oanda"
        name = name[6:]
    elif name.startswith("broker_"):
        meta.source = "broker"
        name = name[7:]

    # Timeframe suffix patterns: M1, M5, M15, M30, H1, H4, D1, W1, etc.
    tf_match = re.search(r'_(m1|m5|m15|m30|h1|h4|d1|w1|mn1)$', name)
    if tf_match:
        meta.timeframe = tf_match.group(1).upper()
        name = name[:tf_match.start()]

    # Symbol: remove underscores that are not part of timeframe
    # Heuristic: if starts with 6 chars like EURUSD, GBPUSD
    meta.symbol = name.upper().replace("_", "")
    if not meta.symbol:
        meta.symbol = "UNKNOWN"
    if meta.source == "UNKNOWN" and "mt5" in filename.lower():
        meta.source = "mt5"
    elif meta.source == "UNKNOWN" and "oanda" in filename.lower():
        meta.source = "oanda"
    elif meta.source == "UNKNOWN":
        meta.source = "csv"
    return meta


def normalize_column_name(col: str) -> str:
    """Map raw column names to normalized schema names."""
    c = col.strip().lower()
    if c in TIMESTAMP_ALIASES:
        return "timestamp"
    if c in REQUIRED_PRICE_COLUMNS:
        return c
    if c in VOLUME_ALIASES:
        if c in ("tick_volume", "tickvol"):
            return "tick_volume"
        return "volume"
    if c in OPTIONAL_COLUMNS:
        return c
    return c


def normalize_row(raw: Dict[str, Any], column_map: Dict[str, str],
                  symbol: Optional[str] = None,
                  timeframe: Optional[str] = None,
                  source: Optional[str] = None) -> Dict[str, Any]:
    """Normalize a single raw CSV row to schema-compliant dict."""
    out: Dict[str, Any] = {}
    for raw_col, value in raw.items():
        norm = column_map.get(raw_col, raw_col)
        out[norm] = value
    # Ensure all schema keys exist with defaults
    for key in NORMALIZED_SCHEMA:
        if key not in out:
            out[key] = None
    if symbol:
        out["symbol"] = symbol
    if timeframe:
        out["timeframe"] = timeframe
    if source:
        out["source"] = source
    return out
