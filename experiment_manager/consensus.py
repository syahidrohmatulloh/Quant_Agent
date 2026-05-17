"""
Consensus engine for multi-strategy signals.
Paper-only. No live trading.
"""
from typing import Dict, Any, List
from experiment_manager.strategy_comparison import normalize_signal


def compute_consensus(comparison_rows, method="majority_vote", minimum_agreement=0.6):
    if not comparison_rows:
        return {
            "consensus_signal": "NEUTRAL",
            "agreement_ratio": 0.0,
            "strategy_count": 0,
            "long_count": 0,
            "short_count": 0,
            "neutral_count": 0,
            "conflict_detected": False,
            "confidence_label": "none",
            "explanation": "No strategies provided.",
        }

    signals = [row.get("signal", "NEUTRAL") for row in comparison_rows]
    total = len(signals)
    long_count = sum(1 for s in signals if s == "LONG")
    short_count = sum(1 for s in signals if s == "SHORT")
    neutral_count = sum(1 for s in signals if s == "NEUTRAL")
    unknown_count = sum(1 for s in signals if s == "UNKNOWN")

    effective_neutral = neutral_count + unknown_count

    long_ratio = long_count / total
    short_ratio = short_count / total
    neutral_ratio = effective_neutral / total

    conflict_detected = (long_count > 0 and short_count > 0)

    consensus_signal = "NEUTRAL"
    agreement_ratio = 0.0
    explanation = ""

    if method == "majority_vote":
        if long_ratio >= minimum_agreement:
            consensus_signal = "LONG"
            agreement_ratio = long_ratio
            explanation = "Majority vote: " + str(long_count) + "/" + str(total) + " strategies signal LONG."
        elif short_ratio >= minimum_agreement:
            consensus_signal = "SHORT"
            agreement_ratio = short_ratio
            explanation = "Majority vote: " + str(short_count) + "/" + str(total) + " strategies signal SHORT."
        else:
            consensus_signal = "NEUTRAL"
            agreement_ratio = max(long_ratio, short_ratio, neutral_ratio)
            explanation = "No majority agreement (threshold " + str(minimum_agreement) + "). Consensus is NEUTRAL."

    elif method == "weighted_vote":
        weights = []
        for row in comparison_rows:
            w = row.get("weight", 0.0) or 0.0
            sig = row.get("signal", "NEUTRAL")
            if sig == "LONG":
                weights.append(w)
            elif sig == "SHORT":
                weights.append(-w)
            else:
                weights.append(0.0)
        total_weight = sum(abs(w) for w in weights)
        if total_weight == 0:
            consensus_signal = "NEUTRAL"
            agreement_ratio = 0.0
            explanation = "Weighted vote: all weights are zero."
        else:
            net_weight = sum(weights)
            agreement_ratio = abs(net_weight) / total_weight
            if agreement_ratio >= minimum_agreement:
                consensus_signal = "LONG" if net_weight > 0 else "SHORT"
                explanation = "Weighted vote: net weight " + str(round(net_weight, 4)) + " (" + str(round(agreement_ratio, 4)) + " agreement)."
            else:
                consensus_signal = "NEUTRAL"
                explanation = "Weighted vote: net weight " + str(round(net_weight, 4)) + " below threshold " + str(minimum_agreement) + "."

    elif method == "conservative":
        if conflict_detected:
            consensus_signal = "NEUTRAL"
            agreement_ratio = max(long_ratio, short_ratio)
            explanation = "Conservative: conflict detected (LONG=" + str(long_count) + ", SHORT=" + str(short_count) + "). Default NEUTRAL."
        elif long_ratio >= minimum_agreement:
            consensus_signal = "LONG"
            agreement_ratio = long_ratio
            explanation = "Conservative: " + str(long_count) + "/" + str(total) + " LONG, no conflict."
        elif short_ratio >= minimum_agreement:
            consensus_signal = "SHORT"
            agreement_ratio = short_ratio
            explanation = "Conservative: " + str(short_count) + "/" + str(total) + " SHORT, no conflict."
        else:
            consensus_signal = "NEUTRAL"
            agreement_ratio = max(long_ratio, short_ratio)
            explanation = "Conservative: no strong agreement (threshold " + str(minimum_agreement) + ")."

    elif method == "unanimous_only":
        if long_count == total and total > 0:
            consensus_signal = "LONG"
            agreement_ratio = 1.0
            explanation = "Unanimous: all " + str(total) + " strategies signal LONG."
        elif short_count == total and total > 0:
            consensus_signal = "SHORT"
            agreement_ratio = 1.0
            explanation = "Unanimous: all " + str(total) + " strategies signal SHORT."
        else:
            consensus_signal = "NEUTRAL"
            agreement_ratio = max(long_ratio, short_ratio)
            explanation = "Unanimous_only: not all strategies agree (" + str(long_count) + " LONG, " + str(short_count) + " SHORT, " + str(effective_neutral) + " NEUTRAL)."

    if agreement_ratio >= 0.8:
        confidence_label = "high"
    elif agreement_ratio >= 0.6:
        confidence_label = "medium"
    elif agreement_ratio >= 0.4:
        confidence_label = "low"
    else:
        confidence_label = "none"

    return {
        "consensus_signal": consensus_signal,
        "agreement_ratio": round(agreement_ratio, 4),
        "strategy_count": total,
        "long_count": long_count,
        "short_count": short_count,
        "neutral_count": neutral_count,
        "conflict_detected": conflict_detected,
        "confidence_label": confidence_label,
        "explanation": explanation,
    }
