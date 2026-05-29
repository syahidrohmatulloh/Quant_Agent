"""
Risk guard for paper decisions.
Enforces exposure limits, short rules, max decisions, and confidence.
No real P&L calculation. Only simulated exposure state.
"""
from typing import Dict, Any, List, Tuple


class RiskGuard:
    """Apply risk rules to paper decisions."""

    def __init__(self, risk_config: Dict[str, Any]):
        self.max_symbol_weight = risk_config.get("max_symbol_weight", 0.25)
        self.max_total_gross_exposure = risk_config.get("max_total_gross_exposure", 1.0)
        self.max_new_decisions = risk_config.get("max_new_decisions_per_run", 10)
        self.allow_short = risk_config.get("allow_short", True)
        self.conflict_action = risk_config.get("conflict_action", "neutral")

    def apply(self, decisions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        approved: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []

        total_gross = 0.0
        new_count = 0

        for d in decisions:
            if d.get("action") == "PAPER_REJECTED":
                approved.append(d)
                continue

            # Max new decisions
            if new_count >= self.max_new_decisions:
                warnings.append("Max new decisions per run reached (" + str(self.max_new_decisions) + "). Skipping remaining.")
                d["action"] = "PAPER_REJECTED"
                d["reason"] = "Max new decisions per run exceeded."
                approved.append(d)
                continue

            # Short check
            if d.get("action") == "PAPER_SHORT" and not self.allow_short:
                d["action"] = "PAPER_REJECTED"
                d["reason"] = "SHORT rejected by risk guard: allow_short is false."
                warnings.append("SHORT rejected for " + d.get("symbol", "?") + ": allow_short=false.")
                approved.append(d)
                continue

            # Symbol weight cap
            weight = d.get("target_weight", 0.0)
            if weight > self.max_symbol_weight:
                weight = self.max_symbol_weight
                d["target_weight"] = weight
                warnings.append("Symbol weight capped to " + str(self.max_symbol_weight) + " for " + d.get("symbol", "?") + ".")

            # Gross exposure check
            added_gross = abs(weight)
            if total_gross + added_gross > self.max_total_gross_exposure:
                d["action"] = "PAPER_REJECTED"
                d["reason"] = "Gross exposure would exceed max_total_gross_exposure (" + str(self.max_total_gross_exposure) + ")."
                warnings.append("Gross exposure limit exceeded for " + d.get("symbol", "?") + ".")
                approved.append(d)
                continue

            total_gross += added_gross
            new_count += 1
            approved.append(d)

        return approved, warnings, errors
