"""Readiness score computation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from typing import Dict, Any


class ReadinessScore:
    def __init__(self) -> None:
        self.score: int = 0
        self.grade: str = "F"
        self.status: str = "NOT_READY"
        self.details: Dict[str, Any] = {}


def compute_readiness_score(
    source_inventory_pass: bool,
    safety_pass_rate: float,
    credential_pass_rate: float,
    execution_gate_pass_rate: float,
    risk_control_pass_rate: float,
    config_pass_rate: float,
    output_hygiene_warnings: int,
    test_status_pass: bool,
) -> ReadinessScore:
    score = ReadinessScore()

    weights = {
        "source_inventory": 10,
        "safety": 15,
        "credential": 15,
        "execution_gate": 20,
        "risk_control": 10,
        "config": 10,
        "output_hygiene": 10,
        "test_status": 10,
    }

    total = 0
    if source_inventory_pass:
        total += weights["source_inventory"]
    total += int(safety_pass_rate * weights["safety"])
    total += int(credential_pass_rate * weights["credential"])
    total += int(execution_gate_pass_rate * weights["execution_gate"])
    total += int(risk_control_pass_rate * weights["risk_control"])
    total += int(config_pass_rate * weights["config"])
    # Deduct for output hygiene warnings
    total -= min(output_hygiene_warnings * 2, weights["output_hygiene"])
    if test_status_pass:
        total += weights["test_status"]

    score.score = max(0, min(100, total))

    if score.score >= 90:
        score.grade = "A"
        score.status = "PAPER_MVP_READY"
    elif score.score >= 80:
        score.grade = "B"
        score.status = "PAPER_MVP_READY_WITH_WARNINGS"
    elif score.score >= 70:
        score.grade = "C"
        score.status = "PAPER_MVP_READY_WITH_WARNINGS"
    elif score.score >= 60:
        score.grade = "D"
        score.status = "NOT_READY"
    else:
        score.grade = "F"
        score.status = "NOT_READY"

    score.details = {
        "source_inventory_pass": source_inventory_pass,
        "safety_pass_rate": safety_pass_rate,
        "credential_pass_rate": credential_pass_rate,
        "execution_gate_pass_rate": execution_gate_pass_rate,
        "risk_control_pass_rate": risk_control_pass_rate,
        "config_pass_rate": config_pass_rate,
        "output_hygiene_warnings": output_hygiene_warnings,
        "test_status_pass": test_status_pass,
    }

    return score
