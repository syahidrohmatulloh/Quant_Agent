"""Source inventory scanner.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import os
from pathlib import Path
from typing import Dict, List, Any


class SourceInventory:
    def __init__(self) -> None:
        self.total_files: int = 0
        self.python_files: int = 0
        self.tool_files: int = 0
        self.test_files: int = 0
        self.example_config_files: int = 0
        self.generated_output_files: int = 0
        self.backup_temp_cache_files: int = 0
        self.files: List[str] = []
        self.warnings: List[str] = []


def build_source_inventory(project_root: Path, include_dirs: List[str], exclude_dirs: List[str]) -> SourceInventory:
    inventory = SourceInventory()
    exclude_set = set(exclude_dirs)

    for inc_dir in include_dirs:
        scan_path = project_root / inc_dir
        if not scan_path.exists():
            inventory.warnings.append(f"Include dir does not exist: {inc_dir}")
            continue

        for root, dirs, files in os.walk(scan_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_set]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_root)
                str_path = str(rel_path)

                inventory.total_files += 1
                inventory.files.append(str_path)

                if file.endswith(".py"):
                    inventory.python_files += 1
                    if str_path.startswith("tools/"):
                        inventory.tool_files += 1
                    if str_path.startswith("tests/"):
                        inventory.test_files += 1

                if file.endswith(".example.json") or file.endswith(".example.txt"):
                    if str_path.startswith("examples/"):
                        inventory.example_config_files += 1

                # Detect generated outputs accidentally present
                if any(part in str_path for part in ["reports/", "logs/", "data/market/", "local_configs/"]):
                    inventory.generated_output_files += 1
                    inventory.warnings.append(f"Generated output found in tracked location: {str_path}")

                # Detect backup/temp/cache files
                if file.endswith(".bak") or ".before-" in file or file.endswith(".tmp") or file.endswith(".swp"):
                    inventory.backup_temp_cache_files += 1
                    inventory.warnings.append(f"Backup/temp/cache file found: {str_path}")

    return inventory
