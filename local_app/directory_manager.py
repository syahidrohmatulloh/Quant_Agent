"""Directory manager for local app.

Creates local generated-output directories.
Does not create or modify data/market unless explicitly configured.
Does not delete anything.
"""

from pathlib import Path
from typing import Any, Dict, List


def create_directories(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    directories = config.get("directories", {})
    created: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    for name, rel_path in directories.items():
        if not isinstance(rel_path, str):
            warnings.append(f"Skipping non-string directory: {name}")
            continue
        target = project_root / rel_path
        try:
            target.mkdir(parents=True, exist_ok=True)
            created.append(str(target.relative_to(project_root)))
        except Exception as e:
            errors.append(f"Failed to create {name}: {e}")

    return {
        "created": created,
        "warnings": warnings,
        "errors": errors,
        "success": len(errors) == 0,
    }
