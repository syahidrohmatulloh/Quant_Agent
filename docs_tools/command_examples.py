"""Curated command examples for documentation CLI tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from typing import Dict, List, Any


class CommandExamples:
    def __init__(self) -> None:
        self.examples: Dict[str, List[str]] = {}


def get_command_examples() -> CommandExamples:
    ce = CommandExamples()
    ce.examples = {
        "test": [
            "python3 -m pytest tests/ -q",
        ],
        "local_workflow": [
            "python3 tools/validate_local_app_config.py --config examples/local_app_config.example.json",
            "python3 tools/run_local_workflow.py --config examples/local_app_config.example.json",
        ],
        "readiness_audit": [
            "python3 tools/validate_readiness_config.py --config examples/readiness_gate_config.example.json",
            "python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing",
        ],
        "dashboard": [
            "python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
            "# Then open http://127.0.0.1:8000 in your browser",
        ],
        "paper_workflow": [
            "python3 tools/run_paper_orchestration.py --config examples/paper_orchestration_config.example.json",
        ],
        "simulator": [
            "python3 tools/run_paper_simulator.py --config examples/paper_simulator_config.example.json",
        ],
        "briefing": [
            "python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json",
        ],
        "cleanup": [
            "python3 tools/cleanup_generated_outputs.py --dry-run",
        ],
    }
    return ce
