"""
Convert Phase 13 consensus results into paper decisions.
No real order. No broker call. Append-only decision log.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_paper_decisions(
    consensus_results: List[Dict[str, Any]],
    run_id: str,
    risk_config: Dict[str, Any],
    decision_policy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Convert consensus results to paper decisions.
    """
    allow_short = risk_config.get("allow_short", True)
    neutral_on_conflict = decision_policy.get("neutral_on_conflict", True)
    min_confidence = decision_policy.get("minimum_consensus_confidence", "medium")
    allow_low = decision_policy.get("allow_low_confidence", False)

    confidence_rank = {"high": 3, "medium": 2, "low": 1, "none": 0}
    min_rank = confidence_rank.get(min_confidence, 2)

    decisions = []
    for sym_res in consensus_results:
        consensus = sym_res.get("consensus", {})
        sym = sym_res.get("symbol", "UNKNOWN")
        tf = sym_res.get("timeframe", "UNKNOWN")
        signal = consensus.get("consensus_signal", "NEUTRAL")
        conf_label = consensus.get("confidence_label", "none")
        conflict = consensus.get("conflict_detected", False)
        agreement = consensus.get("agreement_ratio", 0.0)

        decision_id = str(uuid.uuid4())[:12]
        generated_at = _now_iso()

        # Confidence check
        if confidence_rank.get(conf_label, 0) < min_rank and not allow_low:
            decisions.append({
                "decision_id": decision_id,
                "run_id": run_id,
                "generated_at": generated_at,
                "symbol": sym,
                "timeframe": tf,
                "consensus_signal": signal,
                "confidence_label": conf_label,
                "action": "PAPER_REJECTED",
                "reason": "Confidence below minimum threshold (" + min_confidence + ").",
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
            })
            continue

        # Conflict handling
        if conflict and neutral_on_conflict:
            decisions.append({
                "decision_id": decision_id,
                "run_id": run_id,
                "generated_at": generated_at,
                "symbol": sym,
                "timeframe": tf,
                "consensus_signal": signal,
                "confidence_label": conf_label,
                "action": "PAPER_NEUTRAL",
                "reason": "Conflict detected; neutralized per policy.",
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
            })
            continue

        # Signal mapping
        if signal == "LONG":
            action = "PAPER_LONG"
            reason = "Consensus LONG."
            target_weight = min(agreement, 1.0)
        elif signal == "SHORT":
            if allow_short:
                action = "PAPER_SHORT"
                reason = "Consensus SHORT."
                target_weight = min(agreement, 1.0)
            else:
                action = "PAPER_REJECTED"
                reason = "SHORT consensus rejected because allow_short is false."
                target_weight = 0.0
        elif signal == "NEUTRAL":
            action = "PAPER_NEUTRAL"
            reason = "Consensus NEUTRAL."
            target_weight = 0.0
        else:
            action = "PAPER_HOLD"
            reason = "Unrecognized consensus signal: " + str(signal) + "."
            target_weight = 0.0

        decisions.append({
            "decision_id": decision_id,
            "run_id": run_id,
            "generated_at": generated_at,
            "symbol": sym,
            "timeframe": tf,
            "consensus_signal": signal,
            "confidence_label": conf_label,
            "action": action,
            "reason": reason,
            "target_weight": round(target_weight, 4),
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        })

    return decisions


def append_decisions(decisions: List[Dict[str, Any]], log_path: str) -> None:
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        for d in decisions:
            f.write(__import__("json").dumps(d, default=str) + "\n")
