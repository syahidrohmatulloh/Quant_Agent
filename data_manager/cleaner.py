"""Cleaner - cleans normalized market data CSV."""
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class CleanResult:
    rows_in: int = 0
    rows_out: int = 0
    rows_dropped: int = 0
    duplicate_count: int = 0
    malformed_count: int = 0
    price_anomaly_count: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Cleaner:
    """Cleans canonical market data rows."""

    def clean(self, csv_path: Path, output_path: Optional[Path] = None,
              remove_duplicates: bool = True,
              sort_by_timestamp: bool = True,
              drop_malformed: bool = True,
              drop_non_positive_prices: bool = True,
              fix_column_aliases: bool = True) -> CleanResult:
        if not csv_path.exists():
            raise FileNotFoundError("CSV not found: " + str(csv_path))
        result = CleanResult()
        rows: List[Dict[str, Any]] = []
        seen_timestamps: Set[str] = set()
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                result.rows_in += 1
                clean_row = self._clean_row(row, result, drop_malformed,
                                            drop_non_positive_prices)
                if clean_row is None:
                    result.rows_dropped += 1
                    continue
                ts = clean_row.get("timestamp", "")
                if remove_duplicates and ts in seen_timestamps:
                    result.duplicate_count += 1
                    result.rows_dropped += 1
                    continue
                seen_timestamps.add(ts)
                rows.append(clean_row)
        if sort_by_timestamp:
            try:
                rows.sort(key=lambda r: r.get("timestamp", ""))
            except Exception as e:
                result.warnings.append("Sort failed: " + str(e))
        result.rows_out = len(rows)
        out = output_path or csv_path.parent / (csv_path.stem + "_clean.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            else:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "open", "high", "low", "close"])
                writer.writeheader()
        return result

    def _clean_row(self, row: Dict[str, Any], result: CleanResult,
                   drop_malformed: bool, drop_non_positive: bool) -> Optional[Dict[str, Any]]:
        ts = row.get("timestamp", "").strip()
        if not ts:
            if drop_malformed:
                result.malformed_count += 1
                return None
        ohlc = {}
        for key in ("open", "high", "low", "close"):
            val = row.get(key, "").strip()
            if val == "":
                if drop_malformed:
                    result.malformed_count += 1
                    return None
                ohlc[key] = None
            else:
                try:
                    ohlc[key] = float(val)
                except ValueError:
                    if drop_malformed:
                        result.malformed_count += 1
                        return None
                    ohlc[key] = None
        if drop_non_positive:
            for key, val in ohlc.items():
                if val is not None and val <= 0:
                    result.price_anomaly_count += 1
                    return None
        if (ohlc["high"] is not None and ohlc["low"] is not None
                and ohlc["high"] < ohlc["low"]):
            result.price_anomaly_count += 1
            if drop_malformed:
                return None
        if (ohlc["high"] is not None and ohlc["low"] is not None
                and ohlc["open"] is not None):
            if ohlc["open"] > ohlc["high"] or ohlc["open"] < ohlc["low"]:
                result.price_anomaly_count += 1
                if drop_malformed:
                    return None
        if (ohlc["high"] is not None and ohlc["low"] is not None
                and ohlc["close"] is not None):
            if ohlc["close"] > ohlc["high"] or ohlc["close"] < ohlc["low"]:
                result.price_anomaly_count += 1
                if drop_malformed:
                    return None
        cleaned = dict(row)
        for key in ("open", "high", "low", "close", "volume",
                    "tick_volume", "spread", "real_volume"):
            val = cleaned.get(key, "").strip()
            if val == "":
                cleaned[key] = ""
            else:
                try:
                    float(val)
                    cleaned[key] = val
                except ValueError:
                    cleaned[key] = ""
        cleaned["timestamp"] = ts
        return cleaned
