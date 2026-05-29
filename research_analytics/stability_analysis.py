"""Stability analysis.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import math
from typing import List, Dict, Any, Optional


def analyze_stability(
    returns: List[float],
    signals: Optional[List[Any]] = None,
    rolling_window: int = 20,
    min_periods: int = 10,
) -> Dict[str, Any]:
    n = len(returns)
    rolling_return = []
    rolling_vol = []
    rolling_hit = []
    rolling_dd = []
    signal_stability = []

    for i in range(n):
        start = max(0, i - rolling_window + 1)
        window = returns[start:i + 1]
        if len(window) < min_periods:
            rolling_return.append(None)
            rolling_vol.append(None)
            rolling_hit.append(None)
            rolling_dd.append(None)
            continue
        avg = sum(window) / len(window)
        vol = _std(window)
        hit = sum(1 for r in window if r > 0) / len(window)
        dd = _max_drawdown_of_returns(window)
        rolling_return.append(round(avg, 6))
        rolling_vol.append(round(vol, 6))
        rolling_hit.append(round(hit, 6))
        rolling_dd.append(round(dd, 6))

    if signals:
        norm = [str(s).upper().strip() if s else "NEUTRAL" for s in signals]
        for i in range(n):
            start = max(0, i - rolling_window + 1)
            w = norm[start:i + 1]
            if len(w) < min_periods:
                signal_stability.append(None)
                continue
            changes = sum(1 for j in range(1, len(w)) if w[j] != w[j - 1])
            score = max(0.0, 100.0 - (changes / max(1, len(w) - 1)) * 100.0)
            signal_stability.append(round(score, 2))

    # Degradation warning
    degradation = ""
    if n >= rolling_window * 2:
        first = returns[:n // 2]
        second = returns[n // 2:]
        if first and second:
            avg_first = sum(first) / len(first)
            avg_second = sum(second) / len(second)
            if avg_second < avg_first * 0.5:
                degradation = "Warning: recent simulated performance weaker than earlier period."

    return {
        "rolling_return": rolling_return,
        "rolling_volatility": rolling_vol,
        "rolling_hit_rate": rolling_hit,
        "rolling_drawdown": rolling_dd,
        "signal_stability": signal_stability,
        "degradation_warning": degradation,
        "parameter_sensitivity_placeholder": "Not implemented: pass strategy parameters to compute sensitivity.",
    }


def _std(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)


def _max_drawdown_of_returns(returns: List[float]) -> float:
    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    peak = equity[0]
    max_dd = 0.0
    for val in equity:
        if val > peak:
            peak = val
        dd = (val - peak) / peak if peak != 0 else 0.0
        if dd < max_dd:
            max_dd = dd
    return max_dd
