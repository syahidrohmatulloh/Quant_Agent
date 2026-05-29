"""Versioning - backup and restore dataset versions."""
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class Versioning:
    """Manages dataset backups and restores."""

    def __init__(self, backup_dir: Path) -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_path_for(self, dataset_path: Path) -> Path:
        symbol_tf = dataset_path.stem
        subdir = self.backup_dir / symbol_tf
        subdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return subdir / (ts + "_" + dataset_path.name)

    def backup(self, dataset_path: Path) -> Path:
        if not dataset_path.exists():
            raise FileNotFoundError("Dataset not found: " + str(dataset_path))
        dest = self.backup_path_for(dataset_path)
        shutil.copy2(dataset_path, dest)
        return dest

    def list_versions(self, dataset_path: Path) -> List[Path]:
        symbol_tf = dataset_path.stem
        subdir = self.backup_dir / symbol_tf
        if not subdir.exists():
            return []
        versions = sorted(subdir.glob("*_" + dataset_path.name), key=lambda p: p.name)
        return versions

    def restore(self, dataset_path: Path, version_path: Path,
                confirm: bool = False) -> Path:
        if not confirm:
            raise ValueError("Restore requires explicit --confirm-restore")
        if not version_path.exists():
            raise FileNotFoundError("Version not found: " + str(version_path))
        if dataset_path.exists():
            self.backup(dataset_path)
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(version_path, dataset_path)
        return dataset_path
