"""Tests for Cleaner."""
import csv
import tempfile
from pathlib import Path

from data_manager.cleaner import Cleaner


def _make_csv(tmpdir: Path, headers: list, rows: list) -> Path:
    p = tmpdir / "data.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def test_cleaner_removes_duplicates():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15"],
                       ["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15"],
                       ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25"]])
        cleaner = Cleaner()
        result = cleaner.clean(p, output_path=Path(td) / "out.csv")
        assert result.duplicate_count == 1
        assert result.rows_out == 2


def test_cleaner_sorts_timestamps():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close"],
                      [["2024-01-01T02:00:00", "1.2", "1.3", "1.1", "1.25"],
                       ["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15"]])
        cleaner = Cleaner()
        out = Path(td) / "out.csv"
        cleaner.clean(p, output_path=out)
        with open(out, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["timestamp"] == "2024-01-01T00:00:00"


def test_cleaner_drops_malformed_rows():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close"],
                      [["2024-01-01T00:00:00", "", "1.2", "1.0", "1.15"],
                       ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25"]])
        cleaner = Cleaner()
        result = cleaner.clean(p, output_path=Path(td) / "out.csv")
        assert result.malformed_count == 1
        assert result.rows_out == 1


def test_cleaner_detects_ohlc_anomalies():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close"],
                      [["2024-01-01T00:00:00", "1.1", "1.0", "1.2", "1.15"],
                       ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25"]])
        cleaner = Cleaner()
        result = cleaner.clean(p, output_path=Path(td) / "out.csv")
        assert result.price_anomaly_count >= 1
