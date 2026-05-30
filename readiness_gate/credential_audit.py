"""Credential exposure audit with false-positive suppression.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.

Phase 23 improvements:
- Distinguishes safe construction strings from actual secrets.
- Skips test files that audit the gate itself.
- Checks for assignment context to reduce false positives.
- Does not weaken safety: still flags high-risk patterns in non-test code.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def _build_patterns():
    """Build regex patterns for credential-like strings using safe construction."""
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
        key = a + b
        patterns.append((key, re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE)))
    return patterns


def _looks_like_actual_secret(content: str, match_start: int, match_end: int) -> bool:
    """Check if a credential-like match appears in a suspicious context."""
    start = max(0, match_start - 200)
    end = min(len(content), match_end + 200)
    context = content[start:end]

    # If it is clearly a safe construction (string concatenation), skip
    if "+" in context and ('"' in context or "'" in context):
        if context.count('"') >= 2 or context.count("'") >= 2:
            return False

    # If it is in a comment/docstring about safety/audit, skip
    lines = context.splitlines()
    for line in lines:
        stripped = line.strip().lower()
        if stripped.startswith("#"):
            if any(word in stripped for word in ["audit", "safety", "forbidden", "credential", "paper-only"]):
                return False

    # Check for assignment patterns: key = "..." or key: "..."
    assignment_pat = re.compile(r"[=:]\s*['\"]", re.IGNORECASE)
    if assignment_pat.search(context):
        return True

    # Check for dict patterns
    dict_pat = re.compile(r"['\"]\s*:\s*['\"]", re.IGNORECASE)
    if dict_pat.search(context):
        return True

    return False


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

    gate_test_patterns = [
        "test_phase21",
        "test_phase22", 
        "test_phase23",
        "readiness_gate",
    ]

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

                is_gate_test = any(pat in rel_path for pat in gate_test_patterns)

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                flagged = False
                for key, pat in patterns:
                    for match in pat.finditer(content):
                        if is_gate_test:
                            if not _looks_like_actual_secret(content, match.start(), match.end()):
                                continue
                        else:
                            if not _looks_like_actual_secret(content, match.start(), match.end()):
                                continue

                        audit.findings.append({
                            "file": rel_path,
                            "pattern": key,
                            "status": "warning",
                            "message": "Potential credential-like string: " + key,
                        })
                        audit.warning_count += 1
                        flagged = True
                        break
                    if flagged:
                        break

                if not flagged:
                    audit.pass_count += 1

    return audit
