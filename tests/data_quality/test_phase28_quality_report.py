"""Tests for Phase 28 data quality center module.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import csv
import json
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_quality.quality_report import (
    DataQualityIssue,
    DataQualityFileSummary,
    DataQualityReport,
    _read_csv_rows,
    _detect_timestamp_column,
    _parse_timestamp,
    _has_timezone_info,
    scan_market_data_file,
    scan_market_data_directory,
    classify_data_quality,
    build_data_quality_report,
    render_data_quality_summary,
    write_data_quality_report,
    load_latest_data_quality_report,
)


def _write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TestReadCsvRows:
    def test_reads_valid_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.csv"
            _write_csv(p, [{"timestamp": "2023-01-01", "open": "1.0"}], ["timestamp", "open"])
            rows, error = _read_csv_rows(p)
            assert len(rows) == 1
            assert error is None

    def test_returns_error_for_missing_file(self):
        rows, error = _read_csv_rows(Path("/nonexistent/file.csv"))
        assert not rows
        assert error is not None
        assert "not found" in error.lower()

    def test_returns_error_for_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty.csv"
            p.write_text("", encoding="utf-8")
            rows, error = _read_csv_rows(p)
            assert not rows
            assert error is not None
            assert "empty" in error.lower()


class TestDetectTimestampColumn:
    def test_detects_timestamp(self):
        assert _detect_timestamp_column(["timestamp", "open"]) == "timestamp"

    def test_detects_time(self):
        assert _detect_timestamp_column(["time", "open"]) == "time"

    def test_fallback_first_column(self):
        assert _detect_timestamp_column(["foo", "open"]) == "foo"


class TestParseTimestamp:
    def test_parses_iso(self):
        result = _parse_timestamp("2023-01-15T14:30:00Z")
        assert result is not None
        assert result.year == 2023

    def test_parses_mt5_format(self):
        result = _parse_timestamp("2023.01.15 14:30")
        assert result is not None
        assert result.year == 2023

    def test_returns_none_for_invalid(self):
        assert _parse_timestamp("not-a-date") is None


class TestHasTimezoneInfo:
    def test_detects_z(self):
        assert _has_timezone_info("2023-01-15T14:30:00Z") is True

    def test_detects_offset(self):
        assert _has_timezone_info("2023-01-15T14:30:00+00:00") is True

    def test_no_tz(self):
        assert _has_timezone_info("2023-01-15 14:30:00") is False


class TestScanMarketDataFile:
    def test_valid_file_no_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "EURUSD_H1.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0500", "high": "1.0550", "low": "1.0480", "close": "1.0520", "volume": "1000"},
                {"timestamp": "2023-01-01T11:00:00Z", "open": "1.0520", "high": "1.0580", "low": "1.0500", "close": "1.0550", "volume": "1200"},
            ], ["timestamp", "open", "high", "low", "close", "volume"])
            summary = scan_market_data_file(p)
            assert summary.exists is True
            assert summary.status == "ok"
            assert summary.rows == 2
            assert summary.missing_required_columns == []
            assert summary.duplicate_timestamp_count == 0
            assert summary.non_monotonic == 0
            assert summary.zero_or_negative_price_count == 0
            assert summary.invalid_ohlc_count == 0

    def test_missing_ohlc_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "bad.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "price": "1.05"},
            ], ["timestamp", "price"])
            summary = scan_market_data_file(p)
            assert summary.missing_required_columns
            assert "open" in summary.missing_required_columns
            assert summary.status == "warn"

    def test_duplicate_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "dupes.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"},
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.02", "high": "1.12", "low": "0.92", "close": "1.07"},
            ], ["timestamp", "open", "high", "low", "close"])
            summary = scan_market_data_file(p)
            assert summary.duplicate_timestamp_count == 1

    def test_non_monotonic_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "nonmono.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T11:00:00Z", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"},
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.02", "high": "1.12", "low": "0.92", "close": "1.07"},
            ], ["timestamp", "open", "high", "low", "close"])
            summary = scan_market_data_file(p)
            assert summary.non_monotonic == 1

    def test_zero_negative_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "badprices.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "0.0", "high": "1.1", "low": "0.9", "close": "1.05"},
                {"timestamp": "2023-01-01T11:00:00Z", "open": "-1.0", "high": "1.12", "low": "0.92", "close": "1.07"},
            ], ["timestamp", "open", "high", "low", "close"])
            summary = scan_market_data_file(p)
            assert summary.zero_or_negative_price_count >= 1
            assert summary.status == "warn"

    def test_high_lower_than_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "swap.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0", "high": "0.8", "low": "1.2", "close": "1.05"},
            ], ["timestamp", "open", "high", "low", "close"])
            summary = scan_market_data_file(p)
            assert summary.invalid_ohlc_count >= 1
            assert summary.status == "warn"

    def test_close_outside_high_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "outside.csv"
            _write_csv(p, [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0", "high": "1.1", "low": "1.0", "close": "1.2"},
            ], ["timestamp", "open", "high", "low", "close"])
            summary = scan_market_data_file(p)
            assert summary.invalid_ohlc_count >= 1
            assert summary.status == "warn"

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "empty.csv"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")
            summary = scan_market_data_file(p)
            assert summary.status == "empty"

    def test_malformed_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "data" / "market" / "bad.csv"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\xff\xfe\x00\x01")
            summary = scan_market_data_file(p)
            assert summary.status == "malformed"

    def test_missing_file(self):
        summary = scan_market_data_file(Path("/nonexistent/file.csv"))
        assert summary.status == "missing"
        assert summary.exists is False


class TestScanMarketDataDirectory:
    def test_scans_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            _write_csv(market / "a.csv", [{"timestamp": "2023-01-01T10:00:00Z", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"}], ["timestamp", "open", "high", "low", "close"])
            _write_csv(market / "b.csv", [{"timestamp": "2023-01-01T11:00:00Z", "open": "1.02", "high": "1.12", "low": "0.92", "close": "1.07"}], ["timestamp", "open", "high", "low", "close"])
            summaries = scan_market_data_directory(market)
            assert len(summaries) == 2

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            summaries = scan_market_data_directory(market)
            assert len(summaries) == 0

    def test_nonexistent_directory(self):
        summaries = scan_market_data_directory(Path("/nonexistent"))
        assert len(summaries) == 0


class TestClassifyDataQuality:
    def test_ok_no_issues(self):
        report = DataQualityReport()
        assert classify_data_quality(report) == "OK"

    def test_warn_with_warnings(self):
        report = DataQualityReport()
        report.issues.append(DataQualityIssue(severity="warning", category="test", message="test"))
        assert classify_data_quality(report) == "WARN"

    def test_blocked_with_blockers(self):
        report = DataQualityReport()
        report.issues.append(DataQualityIssue(severity="blocker", category="test", message="test"))
        assert classify_data_quality(report) == "BLOCKED"


class TestBuildDataQualityReport:
    def test_runs_with_no_datasets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {"paper_only": True, "data_only": True, "no_order_submission": True}
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert report.paper_only is True
            assert report.data_only is True
            assert report.no_order_submission is True

    def test_scans_configured_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            _write_csv(market / "EURUSD_H1.csv", [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0500", "high": "1.0550", "low": "1.0480", "close": "1.0520", "volume": "1000"},
            ], ["timestamp", "open", "high", "low", "close", "volume"])
            config = {
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
                "directories": {
                    "market_data_dir": "data/market",
                },
                "quality": {
                    "minimum_rows": 2,
                    "stale_hours": 168,
                },
            }
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert len(report.file_summaries) >= 1
            assert report.files_scanned >= 1

    def test_detects_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
                "directories": {
                    "market_data_dir": "data/nonexistent",
                },
            }
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert any("Optional directory missing" in w for w in report.warnings)

    def test_detects_stale_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            _write_csv(market / "stale.csv", [
                {"timestamp": "2020-01-01T10:00:00Z", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"},
            ], ["timestamp", "open", "high", "low", "close"])
            config = {
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
                "directories": {
                    "market_data_dir": "data/market",
                },
                "quality": {
                    "minimum_rows": 1,
                    "stale_hours": 1,
                },
            }
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert any("stale" in w.lower() for w in report.warnings)

    def test_detects_insufficient_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            _write_csv(market / "small.csv", [
                {"timestamp": "2023-01-01T10:00:00Z", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"},
            ], ["timestamp", "open", "high", "low", "close"])
            config = {
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
                "directories": {
                    "market_data_dir": "data/market",
                },
                "quality": {
                    "minimum_rows": 5,
                    "stale_hours": 168,
                },
            }
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert any("insufficient" in w.lower() for w in report.warnings)

    def test_timezone_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            market = root / "data" / "market"
            market.mkdir(parents=True, exist_ok=True)
            _write_csv(market / "notz.csv", [
                {"timestamp": "2023-01-01 10:00:00", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"},
            ], ["timestamp", "open", "high", "low", "close"])
            config = {
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
                "directories": {
                    "market_data_dir": "data/market",
                },
                "quality": {
                    "minimum_rows": 1,
                    "stale_hours": 168,
                },
            }
            report = build_data_quality_report(root, config=config, allow_missing=True)
            assert any("timezone" in w.lower() or "time zone" in w.lower() for w in report.warnings)


class TestRenderDataQualitySummary:
    def test_includes_paper_only(self):
        report = DataQualityReport()
        text = render_data_quality_summary(report)
        assert "PAPER-ONLY" in text
        assert "DATA-ONLY" in text

    def test_includes_no_live_trading(self):
        report = DataQualityReport()
        text = render_data_quality_summary(report)
        assert "No live trading" in text

    def test_includes_next_safe_commands(self):
        report = DataQualityReport()
        report.next_safe_commands = ["python3 test.py"]
        text = render_data_quality_summary(report)
        assert "python3 test.py" in text

    def test_includes_file_summaries(self):
        report = DataQualityReport()
        report.file_summaries.append(DataQualityFileSummary(path="test.csv", status="ok", rows=10))
        text = render_data_quality_summary(report)
        assert "test.csv" in text
        assert "OK" in text


class TestWriteDataQualityReport:
    def test_writes_json_and_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = DataQualityReport(
                generated_at="2023-01-01T00:00:00Z",
                paper_only=True,
                data_only=True,
                no_order_submission=True,
                status="OK",
                files_scanned=1,
            )
            paths = write_data_quality_report(root, report)
            assert len(paths) == 3
            assert (root / "reports" / "data_quality" / "data_quality_report.json").exists()
            assert (root / "reports" / "data_quality" / "data_quality_report.md").exists()
            assert (root / "reports" / "dashboard" / "data_quality" / "latest.json").exists()


class TestLoadLatestDataQualityReport:
    def test_loads_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = DataQualityReport(
                generated_at="2023-01-01T00:00:00Z",
                paper_only=True,
                data_only=True,
                no_order_submission=True,
                status="OK",
                files_scanned=1,
            )
            write_data_quality_report(root, report)
            loaded = load_latest_data_quality_report(root)
            assert loaded is not None
            assert loaded.status == "OK"
            assert loaded.files_scanned == 1

    def test_returns_none_when_no_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loaded = load_latest_data_quality_report(root)
            assert loaded is None


class TestNoHardcodedPaths:
    def test_no_hardcoded_user_paths_in_source(self):
        source_path = PROJECT_ROOT / "data_quality" / "quality_report.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found: {f}"

    def test_no_forbidden_raw_literals_in_source(self):
        source_path = PROJECT_ROOT / "data_quality" / "quality_report.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"
