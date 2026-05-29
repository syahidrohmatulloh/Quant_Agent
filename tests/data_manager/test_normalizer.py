"""Tests for Normalizer."""
import csv
import tempfile
from pathlib import Path

from data_manager.schema_detector import SchemaDetector
from data_manager.normalizer import Normalizer, CANONICAL_COLUMNS


def _make_csv(tmpdir: Path, headers: list, rows: list) -> Path:
    p = tmpdir / "data.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def test_normalizer_writes_canonical_columns():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["time", "open", "high", "low", "close",
                                  "tick_volume", "spread", "real_volume"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15",
                        "100", "2", "50"]])
        det = SchemaDetector()
        schema = det.detect(p)
        norm = Normalizer()
        out = norm.normalize(p, schema, "EURUSD", "H1", "mt5", output_path=Path(td) / "out.csv")
        with open(out, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        for col in CANONICAL_COLUMNS:
            assert col in row
        assert row["symbol"] == "EURUSD"
        assert row["timeframe"] == "H1"
        assert row["source"] == "mt5"
