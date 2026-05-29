"""
Generate cron-friendly scheduler command.
Does not install cron automatically. Only prints the command.
"""
from pathlib import Path
from typing import Dict, Any


def generate_scheduler_command(config_path: str, project_root: str = ".") -> str:
    """Return a cron-friendly command string for the daily paper workflow."""
    root = Path(project_root).resolve()
    cmd = (
        "cd " + str(root) + " && "
        "python3 tools/run_daily_paper_workflow.py "
        "--config " + str(config_path) + " "
        ">> logs/daily_paper_workflow.log 2>&1"
    )
    return cmd
