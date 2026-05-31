"""Status summary for local app.

Shows phase readiness, latest reports, directories, warnings, next command.
Adds clearer sections for safety mode, local outputs, readiness, briefing,
dashboard, and next safe commands.
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
        "safety_mode": "PAPER-ONLY / DATA-ONLY",
        "phases_ready": {},
        "latest_reports": {},
        "directories": {},
        "local_outputs": {},
        "readiness": {},
        "briefing": {},
        "dashboard": {},
        "warnings": [],
        "next_suggested_command": "",
        "next_safe_commands": [],
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

    # Local outputs summary
    for subdir in ["briefing", "paper_simulator", "dashboard", "local_app", "research_analytics", "data_manager", "readiness_gate"]:
        sub = reports_dir / subdir
        if sub.exists():
            file_count = len(list(sub.glob("*")))
            status["local_outputs"][subdir] = {
                "exists": True,
                "file_count": file_count,
            }
        else:
            status["local_outputs"][subdir] = {
                "exists": False,
                "file_count": 0,
            }

    # Readiness summary
    readiness_json = reports_dir / "readiness_gate" / "readiness_report.json"
    if readiness_json.exists():
        try:
            with open(readiness_json, "r", encoding="utf-8") as f:
                rd = json.load(f)
            score = rd.get("score", {})
            status["readiness"] = {
                "available": True,
                "score": score.get("score"),
                "grade": score.get("grade"),
                "status": score.get("status"),
                "path": str(readiness_json.relative_to(project_root)),
            }
        except Exception:
            status["readiness"] = {"available": False, "error": "Could not parse readiness JSON"}
    else:
        status["readiness"] = {"available": False}
        status["warnings"].append("No readiness report found.")

    # Briefing summary
    briefing_dir = reports_dir / "briefing"
    if briefing_dir.exists():
        files = sorted(briefing_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            status["briefing"] = {
                "available": True,
                "latest": str(files[0].relative_to(project_root)),
            }
        else:
            status["briefing"] = {"available": False}
    else:
        status["briefing"] = {"available": False}

    # Dashboard summary
    dashboard_dir = reports_dir / "dashboard"
    if dashboard_dir.exists():
        files = sorted(dashboard_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            status["dashboard"] = {
                "available": True,
                "latest": str(files[0].relative_to(project_root)),
            }
        else:
            status["dashboard"] = {"available": False}
    else:
        status["dashboard"] = {"available": False}

    # Next suggested command
    status["next_suggested_command"] = (
        "python3 tools/run_local_app_workflow.py "
        "--config examples/local_app_config.example.json --allow-missing"
    )

    # Next safe commands
    dashboard_cfg = config.get("dashboard", {})
    host = dashboard_cfg.get("host", "127.0.0.1")
    port = dashboard_cfg.get("port", 8000)
    status["next_safe_commands"] = [
        "python3 tools/run_operator_day.py --config examples/local_app_config.example.json --allow-missing",
        f"python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
        f"open http://{host}:{port}",
    ]

    return status
