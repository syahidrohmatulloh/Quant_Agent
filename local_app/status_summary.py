"""Status summary for local app.

Shows phase readiness, latest reports, directories, warnings, next command.
No external network.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def build_status(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    directories = config.get("directories", {})
    status: Dict[str, Any] = {
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "phases_ready": {},
        "latest_reports": {},
        "directories": {},
        "warnings": [],
        "next_suggested_command": "",
    }

    # Phase readiness based on directory existence
    phase_dirs = {
        "phase_14_dashboard": directories.get("dashboard", "reports/dashboard"),
        "phase_15_paper_orchestration": "reports/paper_portfolio",
        "phase_16_data_manager": directories.get("data_manager", "reports/data_manager"),
        "phase_17_research_analytics": directories.get("research_analytics", "reports/research_analytics"),
        "phase_18_paper_simulator": directories.get("paper_simulator", "reports/paper_simulator"),
        "phase_19_briefing": directories.get("briefing", "reports/briefing"),
        "phase_20_local_app": "reports/local_app",
    }

    for phase, rel_dir in phase_dirs.items():
        dpath = project_root / rel_dir
        status["phases_ready"][phase] = dpath.exists()

    # Latest reports
    reports_dir = project_root / directories.get("reports", "reports")
    for subdir in ["briefing", "paper_simulator", "dashboard", "local_app", "research_analytics", "data_manager"]:
        sub = reports_dir / subdir
        if sub.exists():
            files = sorted(sub.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            status["latest_reports"][subdir] = str(files[0].relative_to(project_root)) if files else None
        else:
            status["latest_reports"][subdir] = None
            status["warnings"].append(f"Missing report directory: {subdir}")

    # Directory status
    for name, rel_path in directories.items():
        dpath = project_root / rel_path
        status["directories"][name] = {
            "exists": dpath.exists(),
            "path": rel_path,
        }

    # Next suggested command
    status["next_suggested_command"] = (
        "python3 tools/run_local_app_workflow.py "
        "--config examples/local_app_config.example.json --allow-missing"
    )

    return status
