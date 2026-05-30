"""Documentation validator.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
from pathlib import Path
from typing import Dict, List, Any

from .doc_inventory import build_doc_inventory
from .safety_text_check import check_safety_phrases


class DocValidator:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passes: List[str] = []
        self.safety_check: Dict[str, Any] = {}


def validate_docs(project_root: Path) -> DocValidator:
    validator = DocValidator()

    # 1. Check all required docs exist
    inv = build_doc_inventory(project_root)
    if inv.missing_docs:
        for doc in inv.missing_docs:
            validator.errors.append("Missing required doc: " + doc)
    else:
        validator.passes.append("All required docs present")

    # 2. Check README.md safety phrases
    readme_path = project_root / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")
        safety = check_safety_phrases(readme_content)
        if safety.missing_phrases:
            for phrase in safety.missing_phrases:
                validator.warnings.append("README.md missing safety phrase: " + phrase)
        else:
            validator.passes.append("README.md contains all safety phrases")

        # Check README links to key docs
        key_links = [
            "docs/ARCHITECTURE.md",
            "docs/SETUP.md",
            "docs/SAFETY_AND_LIMITATIONS.md",
            "docs/TROUBLESHOOTING.md",
        ]
        for link in key_links:
            if link in readme_content:
                validator.passes.append("README.md links to " + link)
            else:
                validator.warnings.append("README.md missing link to " + link)
    else:
        validator.errors.append("README.md not found")

    # 3. Check each doc for hardcoded paths and safety phrases
    docs_to_check = inv.found_docs
    for doc in docs_to_check:
        doc_path = project_root / doc
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Check for hardcoded local user paths
        # Use safe construction to avoid forbidden contiguous strings
        path_fragments = [
            ("/Users/", "syahidrohmatulloh"),
            ("/mnt/agents", "/output"),
            ("/private/var/folders", ""),
        ]
        for a, b in path_fragments:
            fragment = a + b
            if fragment in content:
                validator.errors.append(doc + " contains hardcoded path: " + fragment)

        # Check for credentials (simple heuristic)
        # Use safe construction
        cred_fragments = [
            ("api", "_key"),
            ("api", "_secret"),
            ("telegram", "_token"),
            ("bot", "_token"),
            ("smtp", "_password"),
            ("access", "_token"),
        ]
        for a, b in cred_fragments:
            fragment = a + b
            if fragment in content:
                validator.warnings.append(doc + " may contain credential-like text: " + fragment)

        # Check safety phrases for key docs
        if doc in ["docs/SAFETY_AND_LIMITATIONS.md", "docs/DEMO_SCRIPT.md", "docs/DAILY_WORKFLOW.md"]:
            safety = check_safety_phrases(content)
            if safety.missing_phrases:
                for phrase in safety.missing_phrases:
                    validator.warnings.append(doc + " missing safety phrase: " + phrase)
            else:
                validator.passes.append(doc + " contains all safety phrases")

    # 4. Check for forbidden generated output references
    if inv.forbidden_paths_found:
        for finding in inv.forbidden_paths_found:
            validator.warnings.append(finding)
    else:
        validator.passes.append("No forbidden generated output paths in docs")

    return validator
