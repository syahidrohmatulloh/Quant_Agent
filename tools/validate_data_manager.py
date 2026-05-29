#!/usr/bin/env python3
"""CLI: validate_data_manager.py - validates Phase 16 modules and tools."""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_file(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print("FAIL " + str(path) + ": " + str(e))
        return False


def main() -> int:
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    ok = 0
    fail = 0
    modules = [
        "data_manager/__init__.py",
        "data_manager/import_config.py",
        "data_manager/schema_detector.py",
        "data_manager/normalizer.py",
        "data_manager/cleaner.py",
        "data_manager/merger.py",
        "data_manager/versioning.py",
        "data_manager/quality_score.py",
        "data_manager/catalog_refresh.py",
        "data_manager/import_log.py",
        "data_manager/importer.py",
    ]
    tools = [
        "tools/validate_import_config.py",
        "tools/import_market_csv.py",
        "tools/merge_market_dataset.py",
        "tools/clean_market_dataset.py",
        "tools/score_market_dataset.py",
        "tools/list_dataset_versions.py",
        "tools/restore_dataset_version.py",
        "tools/validate_data_manager.py",
    ]
    for rel in modules + tools:
        path = PROJECT_ROOT / rel
        if path.exists():
            if check_file(path):
                print("OK   " + rel)
                ok += 1
            else:
                fail += 1
        else:
            print("MISS " + rel)
            fail += 1
    try:
        import data_manager
        print("OK   import data_manager")
        ok += 1
    except Exception as e:
        print("FAIL import data_manager: " + str(e))
        fail += 1
    print("\nSummary: " + str(ok) + " OK, " + str(fail) + " FAIL")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
