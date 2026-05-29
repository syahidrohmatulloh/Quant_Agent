"""Tests for QualityScore."""
import csv
import tempfile
from pathlib import Path

from data_manager.quality_score import QualityScore


def _make_csv(tmpdir: Path, headers: list, rows: list) -> Path:
    p = tmpdir / "data.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def test_quality_score_gives_abc_df():
    with tempfile.TemporaryDirectory() as td:
        p = _make_csv(Path(td), ["timestamp", "open", "high", "low", "close"],
                      [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15"],
                       ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25"]])
        scorer = QualityScore()
        result = scorer.score(p, "EURUSD", "H1", minimum_rows=1)
        assert result.score >= 0 and result.score <= 100
        assert result.grade in ("A", "B", "C", "D", "F")
