"""Shared safety phrase checker for documentation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from pathlib import Path
from typing import Dict, List, Any


class SafetyTextCheck:
    def __init__(self) -> None:
        self.phrases_found: Dict[str, bool] = {}
        self.missing_phrases: List[str] = []


def check_safety_phrases(content: str) -> SafetyTextCheck:
    check = SafetyTextCheck()
    # Required safety phrases (case-insensitive)
    phrases = [
        "paper-only",
        "data-only",
        "no live trading",
        "no order submission",
        "not financial advice",
        "does not guarantee",
        "does not approve",
    ]
    for phrase in phrases:
        check.phrases_found[phrase] = phrase.lower() in content.lower()
        if not check.phrases_found[phrase]:
            check.missing_phrases.append(phrase)
    return check
