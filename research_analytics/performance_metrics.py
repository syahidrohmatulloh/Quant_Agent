"""Performance metrics for research analytics.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Historical simulation only. Past performance does not guarantee future results.
"""
import math
from typing import List, Dict, Any, Optional


def compute_performance_metrics(
    returns: List[float],
    equity: Optional[List[float]] = None,
    signals: Optional[List[str]] = None,
    frequency: Optional[str] = None,
) -> Dict[str, Any]:
    if not returns:
        return {
            "total_return": 0.0,
            "annualized_return": None,
            "volatility": 0.0,
            "downside_volatility": 0.0,
            "sharpe_like": None,
            "sortino_like": None,
            "max_drawdown": 0.0,
            "average_return": 0.0,
            "median_return": 0.0,
            "hit_rate": 0.0,
            "best_period_return": 0.0,
            "worst_period_return": 0.0,
            "number_of_periods": 0,
            "number_of_signals": len(signals) if signals else 0,
            "turnover_estimate": None,
            "note": "Historical simulation only. Past performance does not guarantee future results.",
        }

    n = len(returns)
    total_return = sum(returns)
    avg = total_return / n
    median = _median(returns)
    best = max(returns)
    worst = min(returns)
    hit_rate = sum(1 for r in returns if r > 0) / n

    vol = _std(returns)
    downside_returns = [r for r in returns if r < 0]
    downside_vol = _std(downside_returns) if downside_returns else 0.0

    sharpe_like = avg / vol if vol > 1e-12 else None
    sortino_like = avg / downside_vol if downside_vol > 1e-12 else None

    annualized = None
    if frequency == "daily":
        annualized = avg * 252
    elif frequency == "hourly":
        annualized = avg * 252 * 24
    elif frequency == "weekly":
        annualized = avg * 52
    elif frequency == "monthly":
        annualized = avg * 12

    turnover = None
    if signals:
        changes = sum(1 for i in range(1, len(signals)) if signals[i] != signals[i - 1])
        turnover = changes / max(1, len(signals) - 1)

    return {
        "total_return": round(total_return, 6),
        "annualized_return": round(annualized, 6) if annualized is not None else None,
        "volatility": round(vol, 6),
        "downside_volatility": round(downside_vol, 6),
        "sharpe_like": round(sharpe_like, 6) if sharpe_like is not None else None,
        "sortino_like": round(sortino_like, 6) if sortino_like is not None else None,
        "max_drawdown": 0.0,
        "average_return": round(avg, 6),
        "median_return": round(median, 6),
        "hit_rate": round(hit_rate, 6),
        "best_period_return": round(best, 6),
        "worst_period_return": round(worst, 6),
        "number_of_periods": n,
        "number_of_signals": len(signals) if signals else 0,
        "turnover_estimate": round(turnover, 6) if turnover is not None else None,
        "note": "Historical simulation only. Past performance does not guarantee future results.",
    }


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _std(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)
