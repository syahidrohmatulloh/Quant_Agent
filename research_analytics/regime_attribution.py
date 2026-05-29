"""Regime attribution analysis.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This is research-only and heuristic. Do not claim real macro regime accuracy.
"""
import math
from typing import List, Dict, Any, Optional


def classify_regimes(
    returns: List[float],
    volatility_window: int = 20,
    trend_window: int = 20,
    vol_high: float = 0.015,
    vol_low: float = 0.005,
) -> List[str]:
    n = len(returns)
    regimes = []
    for i in range(n):
        start = max(0, i - volatility_window + 1)
        window = returns[start:i + 1]
        vol = _std(window) if len(window) > 1 else 0.0

        t_start = max(0, i - trend_window + 1)
        t_window = returns[t_start:i + 1]
        trend = sum(t_window) if t_window else 0.0

        if vol > vol_high:
            vol_reg = "high_volatility"
        elif vol < vol_low:
            vol_reg = "low_volatility"
        else:
            vol_reg = "normal_volatility"

        if abs(trend) > vol_high * trend_window:
            trend_reg = "trending" if trend > 0 else "trending"
        else:
            trend_reg = "ranging"

        # Combine heuristically
        if vol_reg == "high_volatility":
            regimes.append("risk_off_like" if trend < 0 else "risk_on_like")
        else:
            regimes.append(vol_reg)
    return regimes


def analyze_regime_attribution(
    returns: List[float],
    signals: Optional[List[Any]] = None,
    regimes: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    if regimes is None:
        regimes = classify_regimes(returns, **kwargs)

    n = len(returns)
    if len(regimes) != n:
        raise ValueError("returns and regimes length mismatch")

    unique = sorted(set(regimes))
    result = {}
    warnings = []
    for reg in unique:
        idx = [i for i, r in enumerate(regimes) if r == reg]
        reg_returns = [returns[i] for i in idx]
        reg_signals = [normalize_signal(signals[i]) for i in idx] if signals else []
        hit = sum(1 for r in reg_returns if r > 0) / len(reg_returns) if reg_returns else 0.0
        dd = analyze_drawdown_for_series(reg_returns)

        result[reg] = {
            "count": len(idx),
            "returns": round(sum(reg_returns), 6) if reg_returns else 0.0,
            "hit_rate": round(hit, 6),
            "signal_count": len(reg_signals),
            "max_drawdown": dd,
        }
        if len(idx) < 10:
            warnings.append(f"Small sample size for regime {reg}: {len(idx)} periods.")

    return {
        "regimes": result,
        "warnings": warnings,
        "note": "Heuristic regime classification for research only. Not real macro regime accuracy.",
    }


def normalize_signal(raw: Any) -> str:
    if raw is None:
        return "NEUTRAL"
    s = str(raw).upper().strip()
    if s in ("LONG", "BUY", "1", "1.0"):
        return "LONG"
    if s in ("SHORT", "SELL", "-1", "-1.0"):
        return "SHORT"
    return "NEUTRAL"


def analyze_drawdown_for_series(returns: List[float]) -> float:
    if not returns:
        return 0.0
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
    return round(max_dd, 6)


def _std(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)
