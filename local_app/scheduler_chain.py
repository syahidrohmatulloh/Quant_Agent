"""Scheduler chain command generator for local app.

Generates a cron-friendly one-line command.
Does not install cron.
Prints review disclaimer.
"""

from pathlib import Path
from typing import Any, Dict


def generate_daily_command(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    scheduler = config.get("scheduler", {})
    default_log = scheduler.get("default_log", "logs/daily_quant_agent_workflow.log")
    suggested_time = scheduler.get("suggested_time", "07:00")
    timezone = scheduler.get("timezone", "Asia/Jakarta")

    # Detect venv python
    venv_python = project_root / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        python_cmd = "python3"
    else:
        python_cmd = str(venv_python.relative_to(project_root))

    # Quote project root if it has spaces
    project_root_str = str(project_root)
    if " " in project_root_str:
        project_root_str = f'"{project_root_str}"'

    config_path = config.get("configs", {}).get("briefing", "examples/local_app_config.example.json")

    command = (
        f"cd {project_root_str} && "
        f"{python_cmd} tools/run_local_app_workflow.py "
        f"--config {config_path} >> {default_log} 2>&1"
    )

    return {
        "command": command,
        "suggested_time": suggested_time,
        "timezone": timezone,
        "log_path": default_log,
        "disclaimer": (
            "This command is printed for review only. "
            "It is NOT installed automatically. "
            "Add it to your crontab manually if desired. "
            "Recommended schedule: after market data update."
        ),
    }
