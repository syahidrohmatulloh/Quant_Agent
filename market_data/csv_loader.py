"""
Load and normalize market CSV files (MT5, generic OHLCV, OANDA/broker exports).
Data-only. No live trading.
"""
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from market_data.csv_schema import (
    TIMESTAMP_ALIASES, REQUIRED_PRICE_COLUMNS, VOLUME_ALIASES,
    TIMESTAMP_FORMATS, normalize_column_name, normalize_row,
    infer_from_filename, InferredMetadata
)


def _parse_timestamp(value: str) -> datetime:
    """Parse timestamp using known formats."""
    value = value.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {value}")


def _detect_columns(headers: List[str]) -> Dict[str, str]:
    """Map raw headers to normalized names."""
    mapping = {}
    for h in headers:
        mapping[h] = normalize_column_name(h)
    return mapping


def load_csv(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load and normalize a market CSV file.
    Returns list of normalized bar dicts.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    if p.stat().st_size == 0:
        raise ValueError("CSV file is empty.")

    inferred = infer_from_filename(p.name)
    sym = symbol or inferred.symbol
    tf = timeframe or inferred.timeframe
    src = source or inferred.source

    rows: List[Dict[str, Any]] = []
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise ValueError("CSV has no headers.")
        col_map = _detect_columns(fieldnames)
        norm_headers = set(col_map.values())

        # Validate required columns exist
        missing = REQUIRED_PRICE_COLUMNS - norm_headers
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Got normalized: {norm_headers}")

        # Find timestamp column
        ts_raw = None
        for h in fieldnames:
            if col_map[h] == "timestamp":
                ts_raw = h
                break
        if ts_raw is None:
            raise ValueError(f"Missing timestamp column. Expected one of: {TIMESTAMP_ALIASES}. Got: {fieldnames}")

        for idx, raw in enumerate(reader, start=2):
            # Skip completely empty rows
            if not any(v.strip() for v in raw.values() if v):
                continue
            try:
                ts = _parse_timestamp(raw[ts_raw])
            except Exception as e:
                raise ValueError(f"Row {idx}: invalid timestamp '{raw.get(ts_raw)}': {e}")

            # Parse numeric columns
            parsed: Dict[str, Any] = {"timestamp": ts}
            for raw_col, norm in col_map.items():
                if norm == "timestamp":
                    continue
                val = raw.get(raw_col, "").strip()
                if norm in ("open", "high", "low", "close", "volume", "tick_volume",
                            "spread", "real_volume"):
                    if val == "":
                        parsed[norm] = None
                    else:
                        try:
                            parsed[norm] = float(val)
                        except ValueError:
                            parsed[norm] = None
                else:
                    parsed[norm] = val

            # Fill metadata
            parsed["symbol"] = sym
            parsed["timeframe"] = tf
            parsed["source"] = src
            rows.append(parsed)

    return rows


def load_csv_strategy_shape(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Load CSV and return {symbol: [bars]} format for strategies."""
    bars = load_csv(path, symbol=symbol, timeframe=timeframe, source=source)
    sym = symbol or (bars[0]["symbol"] if bars else "UNKNOWN")
    return {sym: bars}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load newline-delimited JSON market data."""
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
            # Normalize timestamp
            ts = None
            for key in ("timestamp", "time", "date", "datetime"):
                if key in obj and isinstance(obj[key], str):
                    try:
                        ts = _parse_timestamp(obj[key])
                        break
                    except ValueError:
                        continue
            if ts is None and "timestamp" in obj and isinstance(obj["timestamp"], datetime):
                ts = obj["timestamp"]
            if ts:
                obj["timestamp"] = ts
            rows.append(obj)
    return rows
