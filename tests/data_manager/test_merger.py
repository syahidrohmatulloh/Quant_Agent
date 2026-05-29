"""Tests for Merger."""
import csv
import tempfile
from pathlib import Path

from data_manager.merger import Merger


def _make_csv(tmpdir: Path, name: str, headers: list, rows: list) -> Path:
    p = tmpdir / name
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def test_merger_replace_mode_works():
    with tempfile.TemporaryDirectory() as td:
        target = _make_csv(Path(td), "target.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.0"]])
        source = _make_csv(Path(td), "source.csv", ["timestamp", "open"],
                           [["2024-01-01T01:00:00", "1.1"]])
        merger = Merger()
        result = merger.merge(source, target, mode="replace")
        with open(target, "r") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["timestamp"] == "2024-01-01T01:00:00"


def test_merger_append_mode_works():
    with tempfile.TemporaryDirectory() as td:
        target = _make_csv(Path(td), "target.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.0"]])
        source = _make_csv(Path(td), "source.csv", ["timestamp", "open"],
                           [["2024-01-01T01:00:00", "1.1"]])
        merger = Merger()
        result = merger.merge(source, target, mode="append")
        with open(target, "r") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2


def test_merger_upsert_by_timestamp_works():
    with tempfile.TemporaryDirectory() as td:
        target = _make_csv(Path(td), "target.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.0"]])
        source = _make_csv(Path(td), "source.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.5"],
                            ["2024-01-01T01:00:00", "1.1"]])
        merger = Merger()
        result = merger.merge(source, target, mode="upsert_by_timestamp")
        with open(target, "r") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        ts0 = [r for r in rows if r["timestamp"] == "2024-01-01T00:00:00"][0]
        assert ts0["open"] == "1.5"


def test_merger_backs_up_existing_target():
    with tempfile.TemporaryDirectory() as td:
        target = _make_csv(Path(td), "target.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.0"]])
        source = _make_csv(Path(td), "source.csv", ["timestamp", "open"],
                           [["2024-01-01T01:00:00", "1.1"]])
        merger = Merger()
        result = merger.merge(source, target, mode="upsert_by_timestamp", backup_before_write=True)
        assert result.backup_path is not None
        assert Path(result.backup_path).exists()


def test_merger_preserves_existing_target_if_new_invalid():
    with tempfile.TemporaryDirectory() as td:
        target = _make_csv(Path(td), "target.csv", ["timestamp", "open"],
                           [["2024-01-01T00:00:00", "1.0"]])
        source = _make_csv(Path(td), "source.csv", ["timestamp", "open"], [])
        merger = Merger()
        result = merger.merge(source, target, mode="upsert_by_timestamp",
                              preserve_existing_if_new_invalid=True)
        assert result.preserved_existing
        with open(target, "r") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["timestamp"] == "2024-01-01T00:00:00"
