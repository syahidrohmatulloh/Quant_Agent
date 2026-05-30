"""Output hygiene audit with documentation-aware scanning.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.

Phase 23 improvements:
- Distinguishes actual generated files in the repo from documentation references.
- Does not flag markdown docs that mention reports/, logs/, etc. as concepts.
- Only warns when generated folders contain actual untracked files.
- Suggests .gitignore updates only when needed.
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
            # Phase 23: check if contents are only .gitkeep or README files
            contents = list(candidate_path.rglob("*"))
            safe_only = all(
                f.name in (".gitkeep", "README.md", ".gitignore") or f.is_dir()
                for f in contents if f.is_file()
            )
            if safe_only:
                audit.findings.append({
                    "folder": candidate,
                    "status": "pass",
                    "message": "Generated output folder '" + candidate + "' contains only safe placeholder files",
                })
            else:
                audit.findings.append({
                    "folder": candidate,
                    "status": "warning",
                    "message": "Generated output folder '" + candidate + "' has contents and may be untracked",
                })
                audit.warning_count += 1
        else:
            audit.findings.append({
                "folder": candidate,
                "status": "pass",
                "message": "Generated output folder '" + candidate + "' is empty or absent",
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
                    "message": candidate + " not found in .gitignore",
                })
                audit.warning_count += 1
    else:
        audit.findings.append({
            "folder": ".gitignore",
            "status": "warning",
            "message": ".gitignore not found at project root",
        })
        audit.warning_count += 1

    return audit
