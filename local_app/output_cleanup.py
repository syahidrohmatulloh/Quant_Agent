"""Cleanup generated outputs for local app.

Cleanup generated outputs only.
Requires --confirm-cleanup.
Shows dry-run preview by default.
Never deletes source code, tests, examples, data/market, .git, venv.
Refuses if path is outside project root.
"""

from pathlib import Path
from typing import Any, Dict, List, Set

_SAFE_CLEANUP_DIRS = {
    "reports/briefing",
    "reports/paper_simulator",
    "reports/dashboard/briefing",
    "reports/dashboard/paper_simulator",
    "reports/local_app",
    "logs",
}

_FORBIDDEN_DELETE: Set[str] = {
    "strategies", "tests", "examples", "data/market", "data/raw_imports",
    "local_configs", ".git", "venv", ".env", "local_app", "tools",
    "briefing", "paper_simulator", "paper_orchestration", "data_manager",
    "research_analytics", "dashboard", "market_data", "strategy_lab",
    "backtesting", "broker_integration", "core", "config", "execution",
    "experiment_manager", "live_data", "model_governance", "monitoring",
    "ops", "persistence", "portfolio_optimization", "research",
    "research_pipeline", "risk", "runtime_validation", "scheduler",
    "signal_bridge", "signals", "storage", "streaming",
}


def _is_safe_to_delete(target: Path, project_root: Path) -> bool:
    try:
        target.relative_to(project_root)
    except ValueError:
        return False

    rel = str(target.relative_to(project_root)).replace("\\", "/")
    # Must be within a safe cleanup dir
    in_safe = any(rel.startswith(sd) for sd in _SAFE_CLEANUP_DIRS)
    if not in_safe:
        return False

    # Must not be a forbidden prefix
    parts = rel.split("/")
    for part in parts:
        if part in _FORBIDDEN_DELETE:
            return False

    return True


def preview_cleanup(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    directories = config.get("directories", {})
    to_delete: List[str] = []

    for safe_dir in _SAFE_CLEANUP_DIRS:
        target = project_root / safe_dir
        if target.exists():
            for item in target.rglob("*"):
                if item.is_file():
                    rel = str(item.relative_to(project_root)).replace("\\", "/")
                    to_delete.append(rel)

    return {
        "dry_run": True,
        "would_delete": to_delete,
        "count": len(to_delete),
    }


def perform_cleanup(config: Dict[str, Any], project_root: Path, confirm: bool = False) -> Dict[str, Any]:
    if not confirm:
        return {
            "success": False,
            "error": "Cleanup refused: use --confirm-cleanup to proceed.",
            "dry_run": preview_cleanup(config, project_root),
        }

    directories = config.get("directories", {})
    deleted: List[str] = []
    errors: List[str] = []

    for safe_dir in _SAFE_CLEANUP_DIRS:
        target = project_root / safe_dir
        if not target.exists():
            continue
        for item in list(target.rglob("*")):
            if item.is_file():
                if _is_safe_to_delete(item, project_root):
                    try:
                        rel = str(item.relative_to(project_root)).replace("\\", "/")
                        item.unlink()
                        deleted.append(rel)
                    except Exception as e:
                        errors.append(f"Failed to delete {item}: {e}")
                else:
                    errors.append(f"Refused to delete (not safe): {item}")

    return {
        "success": len(errors) == 0,
        "deleted": deleted,
        "errors": errors,
        "count": len(deleted),
    }
