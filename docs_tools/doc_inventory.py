"""Documentation inventory scanner.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from pathlib import Path
from typing import Dict, List, Any


class DocInventory:
    def __init__(self) -> None:
        self.expected_docs: List[str] = []
        self.found_docs: List[str] = []
        self.missing_docs: List[str] = []
        self.markdown_count: int = 0
        self.forbidden_paths_found: List[str] = []


def build_doc_inventory(project_root: Path) -> DocInventory:
    inv = DocInventory()
    inv.expected_docs = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/SETUP.md",
        "docs/COMMAND_CHEATSHEET.md",
        "docs/DAILY_WORKFLOW.md",
        "docs/DASHBOARD_GUIDE.md",
        "docs/SAFETY_AND_LIMITATIONS.md",
        "docs/TROUBLESHOOTING.md",
        "docs/PHASE_HISTORY.md",
        "docs/DEMO_SCRIPT.md",
        "docs/POST_MVP_ROADMAP.md",
    ]

    for doc in inv.expected_docs:
        doc_path = project_root / doc
        if doc_path.exists():
            inv.found_docs.append(doc)
            inv.markdown_count += 1
        else:
            inv.missing_docs.append(doc)

    # Detect forbidden generated output paths in docs
    forbidden_paths = [
        "reports/",
        "logs/",
        "data/market/",
        "data/raw_imports/",
        "data/market_versions/",
        "local_configs/",
        "backups/",
    ]
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        for md_file in docs_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            for fp in forbidden_paths:
                if fp in content:
                    inv.forbidden_paths_found.append(f"{md_file.relative_to(project_root)} references {fp}")

    return inv
