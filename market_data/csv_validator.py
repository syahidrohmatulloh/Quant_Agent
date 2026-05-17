"""
Validate market CSV files against schema and data quality rules.
Data-only. No live trading.
"""
import math
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from market_data.csv_loader import load_csv
from market_data.csv_schema import (
    REQUIRED_PRICE_COLUMNS, TIMESTAMP_ALIASES, infer_from_filename
)


def _is_bad_number(v: Any) -> bool:
    if v is None:
        return True
    try:
        fv = float(v)
        return math.isnan(fv) or math.isinf(fv)
    except (TypeError, ValueError):
        return True


def _is_future_ts(ts: datetime) -> bool:
    return ts > datetime.now()


def validate_csv(
    path: str,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    min_bars: int = 1,
    expected_tf_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate a market CSV file.
    Returns structured dict with errors, warnings, and metadata.
    """
    p = Path(path)
    errors: List[str] = []
    warnings: List[str] = []
    row_count = 0
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    duplicate_count = 0
    anomaly_count = 0
    gap_count = 0
    bad_price_count = 0
    bad_ts_count = 0
    future_ts_count = 0
    malformed_count = 0

    inferred = infer_from_filename(p.name)
    sym = symbol or inferred.symbol
    tf = timeframe or inferred.timeframe
    src = inferred.source

    # Empty file check
    if not p.exists():
        errors.append(f"File not found: {path}")
        return _build_result(errors, warnings, 0, None, None, sym, tf, src, 0, 0, 0, 0, 0)
    if p.stat().st_size == 0:
        errors.append("File is empty.")
        return _build_result(errors, warnings, 0, None, None, sym, tf, src, 0, 0, 0, 0, 0)

    # Try loading
    try:
        bars = load_csv(path, symbol=symbol, timeframe=timeframe)
    except ValueError as e:
        errors.append(str(e))
        return _build_result(errors, warnings, 0, None, None, sym, tf, src, 0, 0, 0, 0, 0)
    except Exception as e:
        errors.append(f"Load error: {e}")
        return _build_result(errors, warnings, 0, None, None, sym, tf, src, 0, 0, 0, 0, 0)

    row_count = len(bars)
    if row_count == 0:
        errors.append("No data rows found after header.")
        return _build_result(errors, warnings, 0, None, None, sym, tf, src, 0, 0, 0, 0, 0)

    if row_count < min_bars:
        errors.append(f"Insufficient bars: {row_count} < minimum {min_bars}")

    first_ts = bars[0]["timestamp"]
    last_ts = bars[-1]["timestamp"]

    seen_ts: Set[datetime] = set()
    prev_ts: Optional[datetime] = None
    prev_close: Optional[float] = None

    for idx, bar in enumerate(bars):
        ts = bar.get("timestamp")
        if ts is None:
            bad_ts_count += 1
            malformed_count += 1
            continue

        # Future timestamp
        if isinstance(ts, datetime) and _is_future_ts(ts):
            future_ts_count += 1
            warnings.append(f"Row {idx+1}: future timestamp {ts}")

        # Duplicate timestamps
        if isinstance(ts, datetime):
            if ts in seen_ts:
                duplicate_count += 1
                warnings.append(f"Duplicate timestamp: {ts}")
            else:
                seen_ts.add(ts)

        # Monotonic check
        if isinstance(ts, datetime) and prev_ts is not None:
            if ts <= prev_ts:
                warnings.append(f"Non-monotonic timestamp at row {idx+1}: {ts} <= {prev_ts}")

        # OHLC validation
        o = bar.get("open")
        h = bar.get("high")
        l = bar.get("low")
        c = bar.get("close")

        for field_name, val in (("open", o), ("high", h), ("low", l), ("close", c)):
            if _is_bad_number(val):
                bad_price_count += 1
                anomaly_count += 1
                warnings.append(f"Row {idx+1}: bad {field_name} value: {val}")
                continue
            fv = float(val)
            if fv <= 0:
                bad_price_count += 1
                anomaly_count += 1
                warnings.append(f"Row {idx+1}: non-positive {field_name}: {fv}")

        # Only check relationships if all prices are valid numbers
        if not any(_is_bad_number(v) for v in (o, h, l, c)):
            fo, fh, fl, fc = float(o), float(h), float(l), float(c)
            if fh < fl:
                anomaly_count += 1
                warnings.append(f"Row {idx+1}: high ({fh}) < low ({fl})")
            if fo < fl or fo > fh:
                anomaly_count += 1
                warnings.append(f"Row {idx+1}: open ({fo}) outside high-low range")
            if fc < fl or fc > fh:
                anomaly_count += 1
                warnings.append(f"Row {idx+1}: close ({fc}) outside high-low range")

        # Timeframe gap detection
        if isinstance(ts, datetime) and prev_ts is not None and expected_tf_minutes:
            expected_delta = expected_tf_minutes * 60
            actual_delta = (ts - prev_ts).total_seconds()
            # Allow small tolerance for weekends/holidays in daily+ data
            if actual_delta > expected_delta * 2 and actual_delta < expected_delta * 10:
                gap_count += 1
                warnings.append(f"Unexpected gap at row {idx+1}: {actual_delta/60:.0f} min (expected ~{expected_tf_minutes} min)")

        prev_ts = ts if isinstance(ts, datetime) else prev_ts
        prev_close = c if not _is_bad_number(c) else prev_close

    if bad_ts_count > 0:
        warnings.append(f"Bad timestamps: {bad_ts_count}")
    if bad_price_count > 0:
        warnings.append(f"Bad price values: {bad_price_count}")
    if duplicate_count > 0:
        warnings.append(f"Duplicate timestamps: {duplicate_count}")
    if gap_count > 0:
        warnings.append(f"Timeframe gaps detected: {gap_count}")
    if anomaly_count > 0:
        warnings.append(f"Total price anomalies: {anomaly_count}")
    if future_ts_count > 0:
        warnings.append(f"Future timestamps: {future_ts_count}")

    return _build_result(
        errors, warnings, row_count, first_ts, last_ts,
        sym, tf, src, duplicate_count, gap_count, anomaly_count, bad_price_count, future_ts_count
    )


def _build_result(
    errors: List[str],
    warnings: List[str],
    row_count: int,
    first_ts: Optional[datetime],
    last_ts: Optional[datetime],
    symbol: str,
    timeframe: str,
    source: str,
    duplicate_count: int,
    gap_count: int,
    anomaly_count: int,
    bad_price_count: int,
    future_ts_count: int,
) -> Dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": row_count,
        "first_timestamp": first_ts.isoformat() if first_ts else None,
        "last_timestamp": last_ts.isoformat() if last_ts else None,
        "inferred_symbol": symbol,
        "inferred_timeframe": timeframe,
        "inferred_source": source,
        "duplicate_count": duplicate_count,
        "gap_count": gap_count,
        "price_anomaly_count": anomaly_count,
        "bad_price_count": bad_price_count,
        "future_timestamp_count": future_ts_count,
    }
