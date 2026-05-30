"""Safety utilities for local app.

Shared safety checks and constants.
"""

from typing import Set

# Forbidden contiguous strings in source (for reference only; actual avoidance is manual)
PAPER_ONLY_DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def print_disclaimer() -> None:
    print(PAPER_ONLY_DISCLAIMER)
