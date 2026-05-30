"""Output hygiene audit.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from pathlib import Path
from typing import Dict, List, Any


class OutputHygieneAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.warning_count: int = 0


def run_output_hygiene_audit(project_root: Path) -> OutputHygieneAudit:
    audit = OutputHygieneAudit()

    generated_candidates = [
        "reports",
        "logs",
        "data/market",
        "local_configs",
        "backups",
    ]

    for candidate in generated_candidates:
        candidate_path = project_root / candidate
        if candidate_path.exists() and any(candidate_path.iterdir()):
            audit.findings.append({
                "folder": candidate,
                "status": "warning",
                "message": f"Generated output folder '{candidate}' has contents and may be untracked",
            })
            audit.warning_count += 1
        else:
            audit.findings.append({
                "folder": candidate,
                "status": "pass",
                "message": f"Generated output folder '{candidate}' is empty or absent",
            })

    # Suggest .gitignore if needed
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8", errors="ignore")
        for candidate in generated_candidates:
            if candidate not in content:
                audit.findings.append({
                    "folder": candidate,
                    "status": "warning",
                    "message": f"{candidate} not found in .gitignore",
                })
                audit.warning_count += 1

    return audit
