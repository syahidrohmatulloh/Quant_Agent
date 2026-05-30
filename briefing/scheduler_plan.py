"""Generate scheduler command suggestion only.

Does NOT install cron. Does NOT run background services.
Only prints a command string.
"""

from pathlib import Path
from typing import Any, Dict


def generate_scheduler_command(config: Dict[str, Any], project_root: Path, venv_python: str = "python3") -> str:
    config_path = "examples/briefing_config.example.json"
    # Use relative path if possible
    cmd = (
        f"cd {project_root} && "
        f"{venv_python} tools/generate_daily_briefing.py "
        f"--config {config_path} --allow-missing "
        f">> logs/daily_briefing.log 2>&1"
    )
    return cmd


def generate_scheduler_plan(config: Dict[str, Any], project_root: Path, venv_python: str = "python3") -> str:
    cmd = generate_scheduler_command(config, project_root, venv_python)
    lines = [
        "# Scheduler Command Suggestion (not installed automatically)",
        "# Review before enabling. Paper-only / data-only.",
        "#",
        f"# Suggested cron entry (runs daily after paper workflow):",
        f"# 0 7 * * * {cmd}",
        "#",
        "# To install manually:",
        "#   crontab -e",
        "# Then paste the line above (without the leading #).",
        "#",
        "# DISCLAIMER: This is a paper-only briefing system.",
        "# No live trading. No order submission. No real money.",
    ]
    return "\n".join(lines)
