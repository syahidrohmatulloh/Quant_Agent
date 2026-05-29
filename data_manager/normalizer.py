"""Normalizer - converts detected schema to canonical CSV format."""
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema_detector import DetectedSchema


CANONICAL_COLUMNS = [
    "timestamp", "open", "high", "low", "close", "volume",
    "tick_volume", "spread", "real_volume", "symbol", "timeframe", "source"
]


class Normalizer:
    """Normalizes raw CSV into canonical columns."""

    def normalize(self, csv_path: Path, schema: DetectedSchema,
                  symbol: str, timeframe: str, source: str,
                  output_path: Optional[Path] = None) -> Path:
        if not csv_path.exists():
            raise FileNotFoundError("CSV not found: " + str(csv_path))
        rows: List[Dict[str, Any]] = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                canonical: Dict[str, Any] = {}
                ts = row.get(schema.timestamp_col, "") if schema.timestamp_col else ""
                canonical["timestamp"] = self._to_iso(ts)
                for key in ("open", "high", "low", "close"):
                    col = schema.ohlc_cols.get(key)
                    val = row.get(col, "") if col else ""
                    canonical[key] = self._to_float(val)
                canonical["volume"] = self._to_float(
                    row.get(schema.volume_col, "") if schema.volume_col else ""
                )
                canonical["tick_volume"] = self._to_float(
                    row.get(schema.tick_volume_col, "") if schema.tick_volume_col else ""
                )
                canonical["spread"] = self._to_float(
                    row.get(schema.spread_col, "") if schema.spread_col else ""
                )
                canonical["real_volume"] = self._to_float(
                    row.get(schema.real_volume_col, "") if schema.real_volume_col else ""
                )
                canonical["symbol"] = symbol
                canonical["timeframe"] = timeframe
                canonical["source"] = source
                rows.append(canonical)
        out = output_path or csv_path.parent / (csv_path.stem + "_normalized.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CANONICAL_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return out

    def _to_iso(self, val: str) -> str:
        val = val.strip()
        if not val:
            return ""
        if "T" in val:
            return val.replace(" ", "T")
        if " " in val and ":" in val:
            return val.replace(" ", "T")
        return val

    def _to_float(self, val: str) -> str:
        val = val.strip()
        if val == "" or val.lower() == "nan":
            return ""
        try:
            float(val)
            return val
        except ValueError:
            return ""
