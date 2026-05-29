"""Tests for SchemaDetector."""
import csv
import tempfile
from pathlib import Path

from data_manager.schema_detector import SchemaDetector


def _make_csv(tmpdir: Path, headers: list, rows: list) -> Path:
    p = tmpdir / "data.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def test_schema_detector_supports_mt5_columns():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["time", "open", "high", "low", "close",
                                  "tick_volume", "spread", "real_volume"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15",
                        "100", "2", "50"]])
        det = SchemaDetector()
        schema = det.detect(p)
        assert schema.source_format == "mt5"
        assert schema.timestamp_col == "time"
        assert schema.ohlc_cols["open"] == "open"


def test_schema_detector_supports_generic_ohlcv_columns():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close", "volume"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15", "100"]])
        det = SchemaDetector()
        schema = det.detect(p)
        assert schema.source_format == "ohlcv"


def test_schema_detector_is_case_insensitive():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["Time", "Open", "High", "Low", "Close", "Volume"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15", "100"]])
        det = SchemaDetector()
        schema = det.detect(p)
        assert schema.timestamp_col == "Time"
        assert schema.ohlc_cols["open"] == "Open"
