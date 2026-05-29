"""Drawdown analysis.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from typing import List, Dict, Any, Optional


def analyze_drawdown(equity: List[float]) -> Dict[str, Any]:
    if not equity or len(equity) < 2:
        return {
            "equity_curve": equity or [],
            "running_peak": equity or [],
            "drawdown_series": [],
            "max_drawdown": 0.0,
            "max_drawdown_start": None,
            "max_drawdown_end": None,
            "max_drawdown_duration": 0,
            "current_drawdown": 0.0,
            "top_drawdowns": [],
        }

    running_peak = []
    dd_series = []
    peak = equity[0]
    for val in equity:
        if val > peak:
            peak = val
        running_peak.append(peak)
        dd = (val - peak) / peak if peak != 0 else 0.0
        dd_series.append(dd)

    max_dd = 0.0
    max_start = 0
    max_end = 0
    current_start = 0

    for i, dd in enumerate(dd_series):
        if dd == 0.0:
            current_start = i
        if dd < max_dd:
            max_dd = dd
            max_start = current_start
            max_end = i

    current_dd = dd_series[-1]

    # Top N drawdown periods
    drawdowns = _extract_drawdown_periods(dd_series)
    top_5 = sorted(drawdowns, key=lambda x: x["depth"])[:5]

    return {
        "equity_curve": equity,
        "running_peak": running_peak,
        "drawdown_series": [round(d, 6) for d in dd_series],
        "max_drawdown": round(max_dd, 6),
        "max_drawdown_start": max_start,
        "max_drawdown_end": max_end,
        "max_drawdown_duration": max_end - max_start,
        "current_drawdown": round(current_dd, 6),
        "top_drawdowns": top_5,
    }


def _extract_drawdown_periods(dd_series: List[float]) -> List[Dict[str, Any]]:
    periods = []
    in_dd = False
    start = 0
    min_dd = 0.0
    min_idx = 0
    for i, dd in enumerate(dd_series):
        if dd < 0 and not in_dd:
            in_dd = True
            start = i
            min_dd = dd
            min_idx = i
        elif in_dd:
            if dd < min_dd:
                min_dd = dd
                min_idx = i
            if dd == 0.0:
                periods.append({
                    "start": start,
                    "end": i,
                    "depth": round(min_dd, 6),
                    "min_idx": min_idx,
                })
                in_dd = False
    if in_dd:
        periods.append({
            "start": start,
            "end": len(dd_series) - 1,
            "depth": round(min_dd, 6),
            "min_idx": min_idx,
        })
    return periods
