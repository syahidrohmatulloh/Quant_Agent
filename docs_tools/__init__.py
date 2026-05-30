"""Documentation tools for Quant_Agent.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from .doc_inventory import DocInventory, build_doc_inventory
from .doc_validator import DocValidator, validate_docs
from .command_examples import CommandExamples, get_command_examples
from .safety_text_check import SafetyTextCheck, check_safety_phrases

__all__ = [
    "DocInventory",
    "build_doc_inventory",
    "DocValidator",
    "validate_docs",
    "CommandExamples",
    "get_command_examples",
    "SafetyTextCheck",
    "check_safety_phrases",
]
