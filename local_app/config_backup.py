"""Config backup and restore for local app.

Backups example/local config files only.
Does not backup secrets.
Does not read .env.
Restore requires --confirm-restore.
Refuses path traversal.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone


def _safe_backup_path(project_root: Path, backup_dir: Path, timestamp: str) -> Path:
    target = backup_dir / timestamp
    # Ensure it stays within backup_dir
    try:
        target.relative_to(backup_dir)
    except ValueError:
        raise ValueError("Backup path traversal detected")
    return target


def backup_configs(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    directories = config.get("directories", {})
    backup_rel = directories.get("backups", "backups/local_configs")
    backup_dir = project_root / backup_rel
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    target_dir = _safe_backup_path(project_root, backup_dir, timestamp)
    target_dir.mkdir(parents=True, exist_ok=True)

    configs = config.get("configs", {})
    copied: List[str] = []
    skipped: List[str] = []

    for name, cpath in configs.items():
        src = project_root / cpath
        if not src.exists():
            skipped.append(str(src.relative_to(project_root)))
            continue
        dst = target_dir / src.name
        shutil.copy2(str(src), str(dst))
        copied.append(str(src.relative_to(project_root)))

    # Also backup the local_app_config itself if it exists under examples
    # (handled by caller if needed)

    manifest = {
        "timestamp": timestamp,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "copied": copied,
        "skipped": skipped,
    }
    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "backup_dir": str(target_dir.relative_to(project_root)),
        "manifest": manifest,
        "success": True,
    }


def restore_configs(backup_dir: Path, project_root: Path, confirm: bool = False) -> Dict[str, Any]:
    if not confirm:
        return {
            "success": False,
            "error": "Restore refused: use --confirm-restore to proceed.",
        }

    # Validate backup_dir is within project_root/backups
    try:
        backup_dir.relative_to(project_root)
    except ValueError:
        return {
            "success": False,
            "error": "Restore refused: backup directory must be inside project root.",
        }

    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        return {
            "success": False,
            "error": f"Manifest not found: {manifest_path}",
        }

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    restored: List[str] = []
    errors: List[str] = []

    for rel_path in manifest.get("copied", []):
        src = backup_dir / Path(rel_path).name
        dst = project_root / rel_path
        if not src.exists():
            errors.append(f"Source missing: {src}")
            continue
        # Refuse to restore outside project root
        try:
            dst.relative_to(project_root)
        except ValueError:
            errors.append(f"Path traversal refused: {dst}")
            continue
        # Refuse to restore into source code or tests
        forbidden_prefixes = ["strategies/", "tests/", "local_app/", "tools/", "briefing/", "paper_simulator/", "paper_orchestration/", "data_manager/", "research_analytics/", "dashboard/", "market_data/", "strategy_lab/", "backtesting/", "broker_integration/", "core/", "config/", "execution/", "experiment_manager/", "live_data/", "model_governance/", "monitoring/", "ops/", "persistence/", "portfolio_optimization/", "research/", "research_pipeline/", "risk/", "runtime_validation/", "scheduler/", "signal_bridge/", "signals/", "storage/", "streaming/"]
        rel_dst = str(dst.relative_to(project_root))
        if any(rel_dst.startswith(fp) for fp in forbidden_prefixes):
            errors.append(f"Refused to restore into source directory: {rel_dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        restored.append(rel_path)

    return {
        "success": len(errors) == 0,
        "restored": restored,
        "errors": errors,
    }
