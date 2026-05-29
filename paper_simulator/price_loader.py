"""Load canonical CSV price data for paper simulation.

Data-only. No live trading. No network calls.
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from market_data.csv_schema import (
    TIMESTAMP_ALIASES, REQUIRED_PRICE_COLUMNS, VOLUME_ALIASES,
    TIMESTAMP_FORMATS, normalize_column_name, infer_from_filename,
)


def _parse_timestamp(value: str) -> datetime:
    value = value.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError("Cannot parse timestamp: " + value)


class PriceLoader:
    """Load and query price data from canonical CSV."""

    def __init__(self, csv_path: str, symbol: Optional[str] = None, timeframe: Optional[str] = None):
        self.csv_path = csv_path
        self.symbol = symbol
        self.timeframe = timeframe
        self.rows: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        p = Path(self.csv_path)
        if not p.exists():
            raise FileNotFoundError("CSV not found: " + self.csv_path)
        if p.stat().st_size == 0:
            raise ValueError("CSV file is empty.")

        inferred = infer_from_filename(p.name)
        sym = self.symbol or inferred.symbol
        tf = self.timeframe or inferred.timeframe

        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            if not fieldnames:
                raise ValueError("CSV has no headers.")
            col_map = {h: normalize_column_name(h) for h in fieldnames}
            norm_headers = set(col_map.values())

            missing = REQUIRED_PRICE_COLUMNS - norm_headers
            if missing:
                raise ValueError("Missing required columns: " + str(missing) + ". Got: " + str(norm_headers))

            ts_raw = None
            for h in fieldnames:
                if col_map[h] == "timestamp":
                    ts_raw = h
                    break
            if ts_raw is None:
                raise ValueError("Missing timestamp column. Expected one of: " + str(TIMESTAMP_ALIASES))

            for idx, raw in enumerate(reader, start=2):
                if not any(v.strip() for v in raw.values() if v):
                    continue
                try:
                    ts = _parse_timestamp(raw[ts_raw])
                except Exception as e:
                    raise ValueError("Row " + str(idx) + ": invalid timestamp '" + str(raw.get(ts_raw)) + "': " + str(e))

                parsed: Dict[str, Any] = {"timestamp": ts}
                for raw_col, norm in col_map.items():
                    if norm == "timestamp":
                        continue
                    val = raw.get(raw_col, "").strip()
                    if norm in ("open", "high", "low", "close", "volume", "tick_volume", "spread", "real_volume"):
                        if val == "":
                            parsed[norm] = None
                        else:
                            try:
                                parsed[norm] = float(val)
                            except ValueError:
                                parsed[norm] = None
                    else:
                        parsed[norm] = val

                parsed["symbol"] = sym
                parsed["timeframe"] = tf
                parsed["source"] = inferred.source or "csv"
                self.rows.append(parsed)

        # Sort by timestamp ascending
        self.rows.sort(key=lambda r: r["timestamp"])

    def latest_close(self) -> Optional[float]:
        """Return the latest available close price."""
        for row in reversed(self.rows):
            close = row.get("close")
            if close is not None:
                return float(close)
        return None

    def next_close(self, after_timestamp: datetime) -> Optional[float]:
        """Return the first close price after the given timestamp."""
        for row in self.rows:
            if row["timestamp"] > after_timestamp:
                close = row.get("close")
                if close is not None:
                    return float(close)
        return None

    def price_by_timestamp(self, target: datetime) -> Optional[float]:
        """Return close price at exact timestamp if available."""
        for row in self.rows:
            if row["timestamp"] == target:
                close = row.get("close")
                if close is not None:
                    return float(close)
        return None

    def latest_bar(self) -> Optional[Dict[str, Any]]:
        """Return the latest complete bar."""
        if not self.rows:
            return None
        return self.rows[-1]

    def next_bar(self, after_timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Return the first bar after the given timestamp."""
        for row in self.rows:
            if row["timestamp"] > after_timestamp:
                return row
        return None
