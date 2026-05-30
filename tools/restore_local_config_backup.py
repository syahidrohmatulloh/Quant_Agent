#!/usr/bin/env python3
"""Restore local config backup.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from pathlib import Path
import argparse
import json
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DISCLAIMER = "PAPER-ONLY / DATA-ONLY. No live trading. No order submission."


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _safe_target(root: Path, relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Unsafe restore path: " + relative_path)

    target = root / rel
    if not _is_inside(target, root):
        raise ValueError("Restore target outside project root: " + str(target))

    forbidden_roots = {
        ".git",
        "venv",
        "tests",
        "tools",
        "local_app",
        "briefing",
        "paper_simulator",
        "research_analytics",
        "data_manager",
        "paper_orchestration",
    }
    if rel.parts and rel.parts[0] in forbidden_roots:
        raise ValueError("Refusing to restore into source/test/runtime path: " + relative_path)

    return target


def _load_manifest(backup_dir: Path):
    for name in ("manifest.json", "backup_manifest.json"):
        p = backup_dir / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}


def _restore_from_manifest(root: Path, backup_dir: Path, manifest: dict) -> int:
    restored = 0
    files = manifest.get("files", [])

    if isinstance(files, dict):
        files = [
            {"source": backup_name, "target": target_path}
            for target_path, backup_name in files.items()
        ]

    if not isinstance(files, list):
        return 0

    for item in files:
        if isinstance(item, str):
            source_rel = item
            target_rel = item
        elif isinstance(item, dict):
            source_rel = (
                item.get("backup_path")
                or item.get("backup")
                or item.get("source")
                or item.get("filename")
                or item.get("path")
            )
            target_rel = (
                item.get("original_path")
                or item.get("target_path")
                or item.get("target")
                or item.get("relative_path")
                or item.get("path")
            )
        else:
            continue

        if not source_rel or not target_rel:
            continue

        source = Path(source_rel)
        if not source.is_absolute():
            source = backup_dir / source

        if not source.exists() or not source.is_file():
            # Fallback for manifests that store original path but backup file by basename.
            alt = backup_dir / Path(source_rel).name
            if alt.exists() and alt.is_file():
                source = alt
            else:
                continue

        target = _safe_target(root, str(target_rel))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored += 1

    return restored


def _restore_fallback(root: Path, backup_dir: Path) -> int:
    restored = 0

    for source in backup_dir.rglob("*"):
        if not source.is_file():
            continue
        if source.name in {"manifest.json", "backup_manifest.json"}:
            continue

        rel = source.relative_to(backup_dir)

        # If backup preserved examples/... or configs/..., restore same relative path.
        if rel.parts and rel.parts[0] in {"examples", "configs"}:
            target_rel = rel
        else:
            # Otherwise put plain config files back under examples/ by basename.
            target_rel = Path("examples") / source.name

        target = _safe_target(root, str(target_rel))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored += 1

    return restored


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore local config backup.")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--confirm-restore", action="store_true")
    args = parser.parse_args()

    print(DISCLAIMER)
    print()

    if not args.confirm_restore:
        print("FAIL: Restore requires --confirm-restore.")
        return 1

    root = Path(args.project_root).expanduser().resolve()
    backup_dir = Path(args.backup).expanduser().resolve()

    if not root.exists():
        print("FAIL: project root does not exist: " + str(root))
        return 1

    if not backup_dir.exists() or not backup_dir.is_dir():
        print("FAIL: backup directory not found: " + str(backup_dir))
        return 1

    expected_parent = root / "backups" / "local_configs"
    if not _is_inside(backup_dir, expected_parent):
        print("FAIL: Restore refused: backup directory must be inside project root.")
        return 1

    try:
        manifest = _load_manifest(backup_dir)
        restored = _restore_from_manifest(root, backup_dir, manifest)
        if restored == 0:
            restored = _restore_fallback(root, backup_dir)
    except Exception as exc:
        print("FAIL: Restore failed: " + str(exc))
        return 1

    print("Restore complete.")
    print("Files restored:", restored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
