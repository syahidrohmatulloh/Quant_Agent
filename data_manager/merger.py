"""Merger - merges cleaned data into existing dataset."""
import csv
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MergeResult:
    mode: str = ""
    rows_existing: int = 0
    rows_new: int = 0
    rows_out: int = 0
    backup_path: Optional[str] = None
    preserved_existing: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Merger:
    """Merges new rows into existing canonical dataset."""

    def merge(self, new_csv: Path, target_csv: Path,
              mode: str = "upsert_by_timestamp",
              backup_before_write: bool = True,
              preserve_existing_if_new_invalid: bool = True) -> MergeResult:
        result = MergeResult(mode=mode)
        if not new_csv.exists():
            result.errors.append("New CSV not found: " + str(new_csv))
            return result
        new_rows = self._read_rows(new_csv)
        result.rows_new = len(new_rows)
        existing_rows: List[Dict[str, Any]] = []
        if target_csv.exists():
            existing_rows = self._read_rows(target_csv)
            result.rows_existing = len(existing_rows)
        if not new_rows and preserve_existing_if_new_invalid:
            result.preserved_existing = True
            result.warnings.append("New data empty; preserved existing target")
            return result
        if backup_before_write and target_csv.exists():
            backup = self._backup(target_csv)
            result.backup_path = str(backup)
        merged = self._do_merge(existing_rows, new_rows, mode)
        result.rows_out = len(merged)
        temp = target_csv.parent / (target_csv.name + ".tmp")
        target_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(temp, "w", newline="", encoding="utf-8") as f:
            if merged:
                writer = csv.DictWriter(f, fieldnames=list(merged[0].keys()))
                writer.writeheader()
                writer.writerows(merged)
            else:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "open", "high", "low", "close"])
                writer.writeheader()
        temp.replace(target_csv)
        return result

    def _read_rows(self, path: Path) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    def _do_merge(self, existing: List[Dict[str, Any]],
                  new: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
        if mode == "replace":
            return new
        if mode == "append":
            return existing + new
        by_ts: Dict[str, Dict[str, Any]] = {}
        for row in existing:
            ts = row.get("timestamp", "")
            if ts:
                by_ts[ts] = row
        for row in new:
            ts = row.get("timestamp", "")
            if ts:
                by_ts[ts] = row
        merged = list(by_ts.values())
        merged.sort(key=lambda r: r.get("timestamp", ""))
        return merged

    def _backup(self, target: Path) -> Path:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup_name = ts + "_" + target.name
        backup_dir = target.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest = backup_dir / backup_name
        shutil.copy2(target, dest)
        return dest
