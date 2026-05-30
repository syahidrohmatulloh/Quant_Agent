"""Health bundle collector for local app.

Collects environment, module, config, and output status.
Does not fail if git unavailable.
Writes health_check.json.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from local_app.environment_check import check_environment
from local_app.app_config import validate_config


def collect_health(config: Dict[str, Any], project_root: Path, allow_missing: bool = False) -> Dict[str, Any]:
    health: Dict[str, Any] = {
        "timestamp": "",
        "environment": {},
        "modules": {},
        "config_valid": False,
        "directories": {},
        "latest_reports": {},
        "git_status": None,
        "overall": "unknown",
    }

    from datetime import datetime, timezone
    health["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Environment check
    env_result = check_environment(project_root)
    health["environment"] = env_result

    # Config validation
    cfg_result = validate_config(config, allow_missing=allow_missing)
    health["config_valid"] = cfg_result["valid"]
    health["config_errors"] = cfg_result["errors"]
    health["config_warnings"] = cfg_result["warnings"]

    # Directory status
    directories = config.get("directories", {})
    dir_status: Dict[str, Any] = {}
    for name, rel_path in directories.items():
        dpath = project_root / rel_path
        dir_status[name] = {
            "exists": dpath.exists(),
            "path": str(rel_path),
        }
    health["directories"] = dir_status

    # Latest reports
    reports_dir = project_root / directories.get("reports", "reports")
    latest_reports: Dict[str, Any] = {}
    for subdir in ["briefing", "paper_simulator", "dashboard", "local_app", "research_analytics", "data_manager"]:
        sub = reports_dir / subdir
        if sub.exists():
            files = sorted(sub.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            latest_reports[subdir] = str(files[0].relative_to(project_root)) if files else None
        else:
            latest_reports[subdir] = None
    health["latest_reports"] = latest_reports

    # Git status (optional)
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            health["git_status"] = {
                "clean": result.stdout.strip() == "",
                "short_status": result.stdout.strip().split("\n") if result.stdout.strip() else [],
            }
    except Exception:
        health["git_status"] = None

    # Overall
    if env_result.get("healthy") and cfg_result["valid"]:
        health["overall"] = "healthy"
    elif cfg_result["valid"]:
        health["overall"] = "degraded"
    else:
        health["overall"] = "unhealthy"

    # Write output
    out_dir = project_root / directories.get("reports", "reports") / "local_app"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "health_check.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2)

    return health
