"""
Data Quality Center for Phase 28.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Scans market data CSV files and reports quality issues.
Does not modify files. Does not make network calls.
"""

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DataQualityIssue:
    """A single data quality issue."""
    severity: str = "warning"  # info | warning | blocker
    category: str = ""
    path: str = ""
    message: str = ""
    suggested_action: str = ""


@dataclass
class DataQualityFileSummary:
    """Quality summary for a single file."""
    path: str = ""
    exists: bool = False
    file_type: str = "unknown"
    rows: int = 0
    columns: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    latest_timestamp: Optional[str] = None
    duplicate_timestamp_count: int = 0
    non_monotonic: int = 0
    missing_required_columns: List[str] = field(default_factory=list)
    invalid_ohlc_count: int = 0
    zero_or_negative_price_count: int = 0
    gap_count: int = 0
    status: str = "unknown"


@dataclass
class DataQualityReport:
    """Overall data quality report."""
    generated_at: str = ""
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    status: str = "unknown"  # OK | WARN | BLOCKED
    files_scanned: int = 0
    file_summaries: List[DataQualityFileSummary] = field(default_factory=list)
    issues: List[DataQualityIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    data_quality_notes: List[str] = field(default_factory=list)
    generated_outputs: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)


def _read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Read CSV and return rows + error message if malformed."""
    if not path.exists():
        return [], f"File not found: {path}"
    if path.stat().st_size == 0:
        return [], "File is empty"
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                return [], "No header row found"
            rows = []
            for i, row in enumerate(reader, start=2):
                if row is None:
                    continue
                # Skip completely empty rows
                if all(v is None or str(v).strip() == "" for v in row.values()):
                    continue
                rows.append(row)
            return rows, None
    except Exception as e:
        return [], f"CSV parse error: {e}"


def _detect_timestamp_column(fieldnames: List[str]) -> Optional[str]:
    """Heuristically detect the timestamp column name."""
    candidates = ["timestamp", "time", "datetime", "date", "ts", "Timestamp", "Time", "DateTime"]
    for c in candidates:
        if c in fieldnames:
            return c
    return fieldnames[0] if fieldnames else None


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Try to parse a timestamp string into a datetime object."""
    if not value or not value.strip():
        return None
    value = value.strip()
    # ISO-like
    if "T" in value:
        try:
            v = value.replace("Z", "+00:00")
            return datetime.fromisoformat(v)
        except ValueError:
            pass
    # Common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
                "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _has_timezone_info(value: str) -> bool:
    """Check if timestamp string contains timezone info."""
    return "Z" in value or "+" in value[value.find("T"):] if "T" in value else False


def scan_market_data_file(path: Path) -> DataQualityFileSummary:
    """Scan a single market data CSV file for quality issues."""
    summary = DataQualityFileSummary(path=str(path))
    summary.exists = path.exists()

    if not path.exists():
        summary.status = "missing"
        return summary

    if path.stat().st_size == 0:
        summary.status = "empty"
        return summary

    rows, error = _read_csv_rows(path)
    if error:
        summary.status = "malformed"
        return summary

    summary.rows = len(rows)

    if not rows:
        summary.status = "empty"
        return summary

    fieldnames = list(rows[0].keys())
    summary.columns = len(fieldnames)
    summary.file_type = "csv"

    ts_col = _detect_timestamp_column(fieldnames)

    # Check missing OHLC columns
    required = {"open", "high", "low", "close"}
    present = {f.lower() for f in fieldnames}
    missing = required - present
    if missing:
        summary.missing_required_columns = sorted(missing)
        summary.status = "warn"

    # Parse timestamps
    timestamps: List[Tuple[int, Optional[datetime], str]] = []
    for i, row in enumerate(rows, start=2):
        ts_val = row.get(ts_col, "") if ts_col else ""
        ts_dt = _parse_timestamp(ts_val)
        timestamps.append((i, ts_dt, ts_val))

    valid_ts = [(i, ts_dt, ts_val) for i, ts_dt, ts_val in timestamps if ts_dt is not None]

    if valid_ts:
        summary.start_time = valid_ts[0][2]
        summary.end_time = valid_ts[-1][2]
        summary.latest_timestamp = valid_ts[-1][2]

    # Check duplicate timestamps
    seen_ts: Dict[str, int] = {}
    dupes = 0
    for i, ts_dt, ts_val in timestamps:
        if ts_val:
            if ts_val in seen_ts:
                dupes += 1
            seen_ts[ts_val] = i
    summary.duplicate_timestamp_count = dupes

    # Check non-monotonic timestamps
    non_mono = 0
    for j in range(1, len(valid_ts)):
        if valid_ts[j][1] < valid_ts[j-1][1]:
            non_mono += 1
    summary.non_monotonic = non_mono

    # Check price issues
    price_cols = {}
    for canon in ("open", "high", "low", "close"):
        for fn in fieldnames:
            if fn.lower() == canon:
                price_cols[canon] = fn
                break

    zero_neg = 0
    invalid_ohlc = 0

    for i, row in enumerate(rows, start=2):
        prices = {}
        has_all = True
        for canon, fn in price_cols.items():
            val = row.get(fn, "").strip()
            if not val:
                has_all = False
                break
            try:
                prices[canon] = float(val.replace(",", ""))
            except (ValueError, TypeError):
                has_all = False
                break

        if not has_all:
            continue

        # Zero/negative prices
        for canon, price in prices.items():
            if price <= 0:
                zero_neg += 1
                invalid_ohlc += 1
                break

        # high < low
        if "high" in prices and "low" in prices:
            if prices["high"] < prices["low"]:
                invalid_ohlc += 1

        # close outside high/low
        if "close" in prices and "high" in prices and "low" in prices:
            c = prices["close"]
            h = prices["high"]
            l = prices["low"]
            if c > h or c < l:
                invalid_ohlc += 1

    summary.zero_or_negative_price_count = zero_neg
    summary.invalid_ohlc_count = invalid_ohlc

    # Determine status
    if summary.missing_required_columns or summary.zero_or_negative_price_count > 0 or summary.invalid_ohlc_count > 0:
        if summary.status != "warn":
            summary.status = "warn"
    elif summary.duplicate_timestamp_count > 0 or summary.non_monotonic > 0:
        summary.status = "warn"
    else:
        summary.status = "ok"

    return summary


def scan_market_data_directory(path: Path) -> List[DataQualityFileSummary]:
    """Scan all CSV files in a directory."""
    summaries = []
    if not path.exists():
        return summaries
    for f in sorted(path.iterdir()):
        if f.suffix.lower() == ".csv":
            summaries.append(scan_market_data_file(f))
    return summaries


def classify_data_quality(report_or_issues) -> str:
    """Classify overall data quality status from report or issues list."""
    if isinstance(report_or_issues, DataQualityReport):
        issues = report_or_issues.issues
    else:
        issues = report_or_issues

    has_blocker = any(i.severity == "blocker" for i in issues)
    has_warning = any(i.severity == "warning" for i in issues)

    if has_blocker:
        return "BLOCKED"
    elif has_warning:
        return "WARN"
    return "OK"


def build_data_quality_report(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> DataQualityReport:
    """Build a comprehensive data quality report for the project.

    PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
    Does not modify files. Does not make network calls.
    """
    report = DataQualityReport()
    report.generated_at = datetime.now(timezone.utc).isoformat()

    cfg = config or {}
    report.paper_only = bool(cfg.get("paper_only", True))
    report.data_only = bool(cfg.get("data_only", True))
    report.no_order_submission = bool(cfg.get("no_order_submission", True))

    # Scan configured directories
    dirs_to_scan = [
        project_root / "data" / "market",
        project_root / "data" / "raw_imports",
        project_root / "data" / "market_versions",
        project_root / "reports" / "data_manager",
        project_root / "reports" / "dashboard" / "data_manager",
    ]

    # Also scan directories from config if provided
    if cfg.get("directories"):
        for key in ("market_data_dir", "raw_input_dir", "backup_dir"):
            d = cfg["directories"].get(key)
            if d:
                dirs_to_scan.append(project_root / d)

    all_summaries = []
    all_issues = []

    for d in dirs_to_scan:
        if not d.exists():
            if not allow_missing:
                issue = DataQualityIssue(
                    severity="blocker",
                    category="missing_directory",
                    path=str(d),
                    message=f"Required directory missing: {d}",
                    suggested_action=f"Create directory: {d}",
                )
                all_issues.append(issue)
                report.blockers.append(f"Missing directory: {d}")
            else:
                issue = DataQualityIssue(
                    severity="warning",
                    category="missing_directory",
                    path=str(d),
                    message=f"Optional directory missing: {d}",
                    suggested_action=f"Create directory if needed: {d}",
                )
                all_issues.append(issue)
                report.warnings.append(f"Optional directory missing: {d}")
            continue

        summaries = scan_market_data_directory(d)
        all_summaries.extend(summaries)

        for s in summaries:
            if s.status == "missing":
                issue = DataQualityIssue(
                    severity="warning" if allow_missing else "blocker",
                    category="missing_file",
                    path=s.path,
                    message=f"File missing: {s.path}",
                    suggested_action="Check file path or run data collection",
                )
                all_issues.append(issue)
            elif s.status == "empty":
                issue = DataQualityIssue(
                    severity="warning",
                    category="empty_file",
                    path=s.path,
                    message=f"Empty file: {s.path}",
                    suggested_action="Remove or regenerate file",
                )
                all_issues.append(issue)
                report.warnings.append(f"Empty file: {s.path}")
            elif s.status == "malformed":
                issue = DataQualityIssue(
                    severity="warning",
                    category="malformed_csv",
                    path=s.path,
                    message=f"Malformed CSV: {s.path}",
                    suggested_action="Check CSV format and encoding",
                )
                all_issues.append(issue)
                report.warnings.append(f"Malformed CSV: {s.path}")
            elif s.status == "warn":
                if s.missing_required_columns:
                    issue = DataQualityIssue(
                        severity="warning",
                        category="missing_columns",
                        path=s.path,
                        message=f"Missing required columns in {s.path}: {s.missing_required_columns}",
                        suggested_action="Ensure CSV has open, high, low, close columns",
                    )
                    all_issues.append(issue)
                    report.warnings.append(f"Missing columns in {s.path}: {s.missing_required_columns}")

                if s.zero_or_negative_price_count > 0:
                    issue = DataQualityIssue(
                        severity="warning",
                        category="invalid_prices",
                        path=s.path,
                        message=f"{s.zero_or_negative_price_count} zero/negative prices in {s.path}",
                        suggested_action="Check price data for errors",
                    )
                    all_issues.append(issue)
                    report.warnings.append(f"{s.zero_or_negative_price_count} zero/negative prices in {s.path}")

                if s.invalid_ohlc_count > 0:
                    issue = DataQualityIssue(
                        severity="warning",
                        category="invalid_ohlc",
                        path=s.path,
                        message=f"{s.invalid_ohlc_count} invalid OHLC values in {s.path}",
                        suggested_action="Check high >= low and close within range",
                    )
                    all_issues.append(issue)
                    report.warnings.append(f"{s.invalid_ohlc_count} invalid OHLC values in {s.path}")

                if s.duplicate_timestamp_count > 0:
                    issue = DataQualityIssue(
                        severity="info",
                        category="duplicate_timestamps",
                        path=s.path,
                        message=f"{s.duplicate_timestamp_count} duplicate timestamps in {s.path}",
                        suggested_action="Remove duplicate rows",
                    )
                    all_issues.append(issue)

                if s.non_monotonic > 0:
                    issue = DataQualityIssue(
                        severity="warning",
                        category="non_monotonic",
                        path=s.path,
                        message=f"{s.non_monotonic} non-monotonic timestamps in {s.path}",
                        suggested_action="Sort data by timestamp",
                    )
                    all_issues.append(issue)
                    report.warnings.append(f"{s.non_monotonic} non-monotonic timestamps in {s.path}")

    # Check for stale data and insufficient rows
    min_rows = cfg.get("quality", {}).get("minimum_rows", 20) if cfg.get("quality") else 20
    stale_hours = cfg.get("quality", {}).get("stale_hours", 168) if cfg.get("quality") else 168
    now = datetime.now(timezone.utc)

    for s in all_summaries:
        if s.rows > 0 and s.rows < min_rows:
            issue = DataQualityIssue(
                severity="warning",
                category="insufficient_rows",
                path=s.path,
                message=f"Only {s.rows} rows in {s.path} (minimum {min_rows})",
                suggested_action="Collect more data",
            )
            all_issues.append(issue)
            report.warnings.append(f"Insufficient rows in {s.path}: {s.rows} < {min_rows}")

        if s.latest_timestamp:
            ts_dt = _parse_timestamp(s.latest_timestamp)
            if ts_dt:
                if ts_dt.tzinfo is None:
                    ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                age_hours = (now - ts_dt).total_seconds() / 3600
                if age_hours > stale_hours:
                    issue = DataQualityIssue(
                        severity="warning",
                        category="stale_data",
                        path=s.path,
                        message=f"Latest data in {s.path} is {age_hours:.1f} hours old (threshold {stale_hours}h)",
                        suggested_action="Refresh data",
                    )
                    all_issues.append(issue)
                    report.warnings.append(f"Stale data in {s.path}: {age_hours:.1f}h old")

        # Timezone ambiguity
        if s.exists and s.file_type == "csv" and s.rows > 0:
            # Check first few rows for timezone info
            rows_check, _ = _read_csv_rows(Path(s.path))
            ts_col = _detect_timestamp_column(list(rows_check[0].keys()) if rows_check else [])
            tz_ambiguous = 0
            for row in rows_check[:10]:
                ts_val = row.get(ts_col, "") if ts_col else ""
                if ts_val and not _has_timezone_info(ts_val):
                    tz_ambiguous += 1
            if tz_ambiguous > 0:
                issue = DataQualityIssue(
                    severity="info",
                    category="timezone_ambiguity",
                    path=s.path,
                    message=f"Timestamps in {s.path} lack explicit timezone info",
                    suggested_action="Add timezone info to timestamps (e.g., +00:00 or Z)",
                )
                all_issues.append(issue)
                report.warnings.append(f"Timezone ambiguity in {s.path}")

    report.file_summaries = all_summaries
    report.issues = all_issues
    report.files_scanned = len(all_summaries)

    # Determine overall status
    report.status = classify_data_quality(report)

    # Data quality notes
    if not all_summaries:
        report.data_quality_notes.append("No market data files found.")
        if allow_missing:
            report.status = "WARN"
        else:
            report.status = "BLOCKED"
    else:
        ok_count = sum(1 for s in all_summaries if s.status == "ok")
        report.data_quality_notes.append(f"{ok_count}/{len(all_summaries)} files passed basic checks.")

    report.next_safe_commands = [
        "python3 tools/show_data_quality.py --config examples/market_data_import_config.example.json --allow-missing",
        "python3 tools/run_data_import_pipeline.py --config examples/market_data_import_config.example.json",
        "python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
    ]

    return report


def render_data_quality_summary(report: DataQualityReport) -> str:
    """Render DataQualityReport as a human-readable CLI string."""
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT DATA QUALITY CENTER",
        "=" * 60,
        "",
        " PAPER-ONLY / DATA-ONLY",
        " No live trading. No order submission.",
        " This is not financial advice.",
        " This does not approve or enable live trading.",
        "",
        f" Generated: {report.generated_at}",
        f" Status: {report.status}",
        f" Files scanned: {report.files_scanned}",
        "",
    ]

    for s in report.file_summaries:
        status_icon = "OK" if s.status == "ok" else ("WARN" if s.status == "warn" else s.status.upper())
        lines.append(f" [{status_icon}] {s.path}")
        lines.append(f"     Type: {s.file_type} | Rows: {s.rows} | Columns: {s.columns}")
        if s.start_time and s.end_time:
            lines.append(f"     Time range: {s.start_time} to {s.end_time}")
        if s.latest_timestamp:
            lines.append(f"     Latest: {s.latest_timestamp}")
        if s.duplicate_timestamp_count > 0:
            lines.append(f"     Duplicates: {s.duplicate_timestamp_count}")
        if s.non_monotonic > 0:
            lines.append(f"     Non-monotonic: {s.non_monotonic}")
        if s.missing_required_columns:
            lines.append(f"     Missing columns: {s.missing_required_columns}")
        if s.zero_or_negative_price_count > 0:
            lines.append(f"     Zero/negative prices: {s.zero_or_negative_price_count}")
        if s.invalid_ohlc_count > 0:
            lines.append(f"     Invalid OHLC: {s.invalid_ohlc_count}")
        lines.append("")

    if report.issues:
        lines.append(f" Issues ({len(report.issues)}):")
        for issue in report.issues:
            lines.append(f" [{issue.severity.upper()}] {issue.category}: {issue.message}")
            if issue.suggested_action:
                lines.append(f"     Action: {issue.suggested_action}")
        lines.append("")

    if report.warnings:
        lines.append(f" Warnings ({len(report.warnings)}):")
        for w in report.warnings:
            lines.append(f" - {w}")
        lines.append("")

    if report.blockers:
        lines.append(f" Blockers ({len(report.blockers)}):")
        for b in report.blockers:
            lines.append(f" ! {b}")
        lines.append("")

    if report.data_quality_notes:
        lines.append(" Data Quality Notes:")
        for note in report.data_quality_notes:
            lines.append(f" • {note}")
        lines.append("")

    lines.append(" Next Safe Commands")
    lines.append("-" * 40)
    for cmd in report.next_safe_commands:
        lines.append(f" $ {cmd}")
    lines.append("")

    lines.append(" Reminder: reports/logs/local outputs should not be committed.")
    lines.append(" This tool does not approve or enable live trading.")
    lines.append(" No broker calls. No live network. No credential prompts.")
    lines.append(" No actual email send. No actual Telegram send. No cron install.")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)


def write_data_quality_report(
    project_root: Path,
    report: DataQualityReport,
    config: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Write data quality report to disk.

    Writes:
    - reports/data_quality/data_quality_report.json
    - reports/data_quality/data_quality_report.md
    - reports/dashboard/data_quality/latest.json
    """
    output_paths = []

    # JSON report
    json_dir = project_root / "reports" / "data_quality"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "data_quality_report.json"

    report_dict = {
        "generated_at": report.generated_at,
        "paper_only": report.paper_only,
        "data_only": report.data_only,
        "no_order_submission": report.no_order_submission,
        "status": report.status,
        "files_scanned": report.files_scanned,
        "file_summaries": [
            {
                "path": s.path,
                "exists": s.exists,
                "file_type": s.file_type,
                "rows": s.rows,
                "columns": s.columns,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "latest_timestamp": s.latest_timestamp,
                "duplicate_timestamp_count": s.duplicate_timestamp_count,
                "non_monotonic": s.non_monotonic,
                "missing_required_columns": s.missing_required_columns,
                "invalid_ohlc_count": s.invalid_ohlc_count,
                "zero_or_negative_price_count": s.zero_or_negative_price_count,
                "gap_count": s.gap_count,
                "status": s.status,
            }
            for s in report.file_summaries
        ],
        "issues": [
            {
                "severity": i.severity,
                "category": i.category,
                "path": i.path,
                "message": i.message,
                "suggested_action": i.suggested_action,
            }
            for i in report.issues
        ],
        "warnings": report.warnings,
        "blockers": report.blockers,
        "data_quality_notes": report.data_quality_notes,
        "next_safe_commands": report.next_safe_commands,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    output_paths.append(str(json_path))

    # Markdown report
    md_path = json_dir / "data_quality_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_data_quality_summary(report))
    output_paths.append(str(md_path))

    # Dashboard latest JSON
    dash_dir = project_root / "reports" / "dashboard" / "data_quality"
    dash_dir.mkdir(parents=True, exist_ok=True)
    dash_path = dash_dir / "latest.json"
    with open(dash_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    output_paths.append(str(dash_path))

    report.generated_outputs = output_paths
    return output_paths


def load_latest_data_quality_report(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[DataQualityReport]:
    """Load the latest data quality report from disk."""
    json_path = project_root / "reports" / "data_quality" / "data_quality_report.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = DataQualityReport(
            generated_at=data.get("generated_at", ""),
            paper_only=data.get("paper_only", True),
            data_only=data.get("data_only", True),
            no_order_submission=data.get("no_order_submission", True),
            status=data.get("status", "unknown"),
            files_scanned=data.get("files_scanned", 0),
            warnings=data.get("warnings", []),
            blockers=data.get("blockers", []),
            data_quality_notes=data.get("data_quality_notes", []),
            next_safe_commands=data.get("next_safe_commands", []),
        )

        for s in data.get("file_summaries", []):
            report.file_summaries.append(DataQualityFileSummary(
                path=s.get("path", ""),
                exists=s.get("exists", False),
                file_type=s.get("file_type", "unknown"),
                rows=s.get("rows", 0),
                columns=s.get("columns", 0),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                latest_timestamp=s.get("latest_timestamp"),
                duplicate_timestamp_count=s.get("duplicate_timestamp_count", 0),
                non_monotonic=s.get("non_monotonic", 0),
                missing_required_columns=s.get("missing_required_columns", []),
                invalid_ohlc_count=s.get("invalid_ohlc_count", 0),
                zero_or_negative_price_count=s.get("zero_or_negative_price_count", 0),
                gap_count=s.get("gap_count", 0),
                status=s.get("status", "unknown"),
            ))

        for i in data.get("issues", []):
            report.issues.append(DataQualityIssue(
                severity=i.get("severity", "warning"),
                category=i.get("category", ""),
                path=i.get("path", ""),
                message=i.get("message", ""),
                suggested_action=i.get("suggested_action", ""),
            ))

        return report
    except Exception:
        return None
