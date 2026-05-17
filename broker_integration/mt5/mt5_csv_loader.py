"""
Load OHLCV CSV exported from MetaTrader 5 without requiring the MetaTrader5 package.
Data-only. No order execution. No live trading.
"""
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


def _parse_timestamp(value: str) -> datetime:
    """Parse common MT5 CSV timestamp formats."""
    formats = [
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y%m%d %H:%M:%S",
        "%Y%m%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {value}")


REQUIRED_COLUMNS = {"open", "high", "low", "close"}
OPTIONAL_COLUMNS = {"tick_volume", "volume", "spread", "real_volume"}
TIMESTAMP_ALIASES = {"time", "timestamp", "datetime", "date"}


def load_mt5_csv(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load and normalize MT5-exported OHLCV CSV.
    Accepts columns: time/timestamp, open, high, low, close, tick_volume/volume, spread, real_volume.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    rows: List[Dict[str, Any]] = []
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])

        # Find timestamp column
        ts_col = None
        for alias in TIMESTAMP_ALIASES:
            if alias in headers:
                ts_col = alias
                break
        if ts_col is None:
            raise ValueError(f"Missing timestamp column. Expected one of: {TIMESTAMP_ALIASES}. Got: {headers}")

        # Check required columns
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Got: {headers}")

        for row in reader:
            ts = _parse_timestamp(row[ts_col])
            entry = {
                "timestamp": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "tick_volume": int(float(row.get("tick_volume", row.get("volume", 0)))),
                "spread": int(float(row.get("spread", 0))),
                "real_volume": int(float(row.get("real_volume", 0))),
                "symbol": symbol or "UNKNOWN",
                "timeframe": timeframe or "UNKNOWN",
                "source": "mt5_csv",
            }
            rows.append(entry)

    return rows


def load_mt5_csv_multi(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load MT5 CSV and return in strategy-compatible shape {symbol: [bars]}.
    """
    bars = load_mt5_csv(path, symbol=symbol, timeframe=timeframe)
    sym = symbol or (bars[0]["symbol"] if bars else "UNKNOWN")
    return {sym: bars}


def load_mt5_csvl(path: str) -> List[Dict[str, Any]]:
    """Load JSONL (newline-delimited JSON) exported from MT5."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSONL not found: {path}")
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            # Normalize timestamp if string
            if isinstance(obj.get("timestamp"), str):
                obj["timestamp"] = _parse_timestamp(obj["timestamp"])
            elif isinstance(obj.get("time"), str):
                obj["timestamp"] = _parse_timestamp(obj.pop("time"))
            rows.append(obj)
    return rows
