"""Signal quality analysis.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from typing import List, Dict, Any, Optional


def normalize_signal(raw: Any) -> str:
    if raw is None:
        return "NEUTRAL"
    s = str(raw).upper().strip()
    if s in ("LONG", "BUY", "1", "1.0"):
        return "LONG"
    if s in ("SHORT", "SELL", "-1", "-1.0"):
        return "SHORT"
    return "NEUTRAL"


def analyze_signal_quality(
    signals: List[Any],
    returns: Optional[List[float]] = None,
    forward_periods: int = 1,
) -> Dict[str, Any]:
    norm = [normalize_signal(s) for s in signals]
    n = len(norm)

    long_count = sum(1 for s in norm if s == "LONG")
    short_count = sum(1 for s in norm if s == "SHORT")
    neutral_count = sum(1 for s in norm if s == "NEUTRAL")
    changes = sum(1 for i in range(1, n) if norm[i] != norm[i - 1])

    avg_fwd = {"LONG": None, "SHORT": None, "NEUTRAL": None}
    hit_by = {"LONG": None, "SHORT": None, "NEUTRAL": None}
    fp_like = 0
    fn_like = 0

    if returns and len(returns) >= n + forward_periods:
        for label in ("LONG", "SHORT", "NEUTRAL"):
            fwd = []
            for i in range(n):
                if norm[i] == label:
                    fwd.append(returns[i + forward_periods - 1])
            if fwd:
                avg_fwd[label] = round(sum(fwd) / len(fwd), 6)
                hit_by[label] = round(sum(1 for r in fwd if r > 0) / len(fwd), 6)

        # False-positive-like: signal LONG but forward return <= 0
        # False-negative-like: signal SHORT but forward return >= 0
        for i in range(n - forward_periods):
            fwd_r = returns[i + forward_periods]
            if norm[i] == "LONG" and fwd_r <= 0:
                fp_like += 1
            if norm[i] == "SHORT" and fwd_r >= 0:
                fn_like += 1

    # Signal stability score 0-100
    stability = 100.0
    if n > 1:
        flip_rate = changes / (n - 1)
        stability = max(0.0, 100.0 - (flip_rate * 100.0))

    # Average holding period estimate
    holding = None
    if changes > 0:
        holding = n / changes

    conflict = ""
    if changes > n * 0.3:
        conflict = "Warning: signal flips frequently (>30% of periods)."

    return {
        "signal_count": n,
        "long_count": long_count,
        "short_count": short_count,
        "neutral_count": neutral_count,
        "signal_change_count": changes,
        "average_forward_return_by_signal": avg_fwd,
        "hit_rate_by_signal": hit_by,
        "false_positive_like": fp_like,
        "false_negative_like": fn_like,
        "average_holding_period_estimate": round(holding, 2) if holding else None,
        "signal_stability_score": round(stability, 2),
        "conflict_warning": conflict,
    }
