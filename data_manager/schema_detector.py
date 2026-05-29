"""SchemaDetector - detects CSV schema from common market data formats."""
import csv
from pathlib import Path
from typing import Dict, List, Optional


class DetectedSchema:
    def __init__(self, source_format: str, columns: List[str],
                 timestamp_col: Optional[str] = None,
                 ohlc_cols: Dict[str, str] = None,
                 volume_col: Optional[str] = None,
                 tick_volume_col: Optional[str] = None,
                 spread_col: Optional[str] = None,
                 real_volume_col: Optional[str] = None) -> None:
        self.source_format = source_format
        self.columns = columns
        self.timestamp_col = timestamp_col
        self.ohlc_cols = ohlc_cols or {}
        self.volume_col = volume_col
        self.tick_volume_col = tick_volume_col
        self.spread_col = spread_col
        self.real_volume_col = real_volume_col


class SchemaDetector:
    """Detects schema from MT5, generic OHLCV, OANDA-like CSVs."""

    TIMESTAMP_ALIASES: List[str] = [
        "time", "timestamp", "date", "datetime", "Time", "Timestamp",
        "Date", "Datetime", "TIME", "TIMESTAMP", "DATE", "DATETIME"
    ]
    OHLC_ALIASES: Dict[str, List[str]] = {
        "open": ["open", "Open", "OPEN", "o", "O", "bid_open", "mid_open", "ask_open"],
        "high": ["high", "High", "HIGH", "h", "H", "bid_high", "mid_high", "ask_high"],
        "low": ["low", "Low", "LOW", "l", "L", "bid_low", "mid_low", "ask_low"],
        "close": ["close", "Close", "CLOSE", "c", "C", "bid_close", "mid_close", "ask_close"],
    }
    VOLUME_ALIASES: List[str] = ["volume", "Volume", "VOLUME", "vol", "Vol", "VOL"]
    TICK_VOLUME_ALIASES: List[str] = [
        "tick_volume", "tick volume", "Tick Volume",
        "Tick_Volume", "TICK_VOLUME", "tickvolume"
    ]
    SPREAD_ALIASES: List[str] = ["spread", "Spread", "SPREAD"]
    REAL_VOLUME_ALIASES: List[str] = [
        "real_volume", "real volume", "Real Volume",
        "Real_Volume", "REAL_VOLUME", "realvolume"
    ]

    def detect(self, csv_path: Path) -> DetectedSchema:
        if not csv_path.exists():
            raise FileNotFoundError("CSV not found: " + str(csv_path))
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []
        headers = [h.strip() for h in headers]
        lower_headers = [h.lower().replace(" ", "_") for h in headers]

        source_format = self._guess_format(headers, lower_headers)
        timestamp_col = self._find_column(headers, self.TIMESTAMP_ALIASES)
        ohlc_cols = {}
        for key, aliases in self.OHLC_ALIASES.items():
            col = self._find_column(headers, aliases)
            if col:
                ohlc_cols[key] = col
        volume_col = self._find_column(headers, self.VOLUME_ALIASES)
        tick_volume_col = self._find_column(headers, self.TICK_VOLUME_ALIASES)
        spread_col = self._find_column(headers, self.SPREAD_ALIASES)
        real_volume_col = self._find_column(headers, self.REAL_VOLUME_ALIASES)

        return DetectedSchema(
            source_format=source_format,
            columns=headers,
            timestamp_col=timestamp_col,
            ohlc_cols=ohlc_cols,
            volume_col=volume_col,
            tick_volume_col=tick_volume_col,
            spread_col=spread_col,
            real_volume_col=real_volume_col,
        )

    def _guess_format(self, headers: List[str], lower_headers: List[str]) -> str:
        mt5_cols = {"time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"}
        if mt5_cols.issubset(set(lower_headers)):
            return "mt5"
        ohlcv = {"timestamp", "open", "high", "low", "close", "volume"}
        if ohlcv.issubset(set(lower_headers)):
            return "ohlcv"
        if any(h.lower() in {"bid", "ask", "mid"} for h in headers):
            return "oanda_like"
        return "generic"

    def _find_column(self, headers: List[str], aliases: List[str]) -> Optional[str]:
        for alias in aliases:
            for h in headers:
                if h.lower().replace(" ", "_") == alias.lower().replace(" ", "_"):
                    return h
        return None
