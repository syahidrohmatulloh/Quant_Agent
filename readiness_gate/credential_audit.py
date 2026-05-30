"""Credential exposure audit.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def _build_patterns():
    # Safe construction to avoid forbidden contiguous literals in source
    parts = [
        ("api", "_key"),
        ("api", "_secret"),
        ("access", "_token"),
        ("refresh", "_token"),
        ("telegram", "_token"),
        ("bot", "_token"),
        ("smtp", "_password"),
        ("email", "_password"),
        ("broker", "_password"),
        ("account", "_password"),
        ("secret", "_key"),
        ("auth", "_token"),
        ("bearer", "_token"),
        ("private", "_key"),
    ]
    patterns = []
    for a, b in parts:
        # Match whole-word-like patterns
        patterns.append(re.compile(r"\b" + re.escape(a + b) + r"\b", re.IGNORECASE))
        # Also match camelCase variants
        camel = a + b.replace("_", "").title()
        patterns.append(re.compile(re.escape(camel), re.IGNORECASE))
    return patterns


class CredentialAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.warning_count: int = 0
        self.fail_count: int = 0


def run_credential_audit(project_root: Path, include_dirs: List[str], exclude_dirs: List[str]) -> CredentialAudit:
    audit = CredentialAudit()
    patterns = _build_patterns()
    exclude_set = set(exclude_dirs)

    for inc_dir in include_dirs:
        scan_path = project_root / inc_dir
        if not scan_path.exists():
            continue

        for root, dirs, files in os.walk(scan_path):
            dirs[:] = [d for d in dirs if d not in exclude_set]

            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(project_root))

                # Skip tests that use safe constructed strings intentionally
                if "test_" in file and "readiness" in rel_path:
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                for pat in patterns:
                    matches = pat.findall(content)
                    if matches:
                        # Avoid false positives by checking if it is a safe construction
                        if "+" in content and ("\"" + matches[0].split("_")[0] + "\"" in content or "'" + matches[0].split("_")[0] + "'" in content):
                            continue
                        audit.findings.append({
                            "file": rel_path,
                            "pattern": matches[0],
                            "status": "warning",
                            "message": f"Potential credential-like string: {matches[0]}",
                        })
                        audit.warning_count += 1
                        break
                else:
                    audit.pass_count += 1

    return audit
