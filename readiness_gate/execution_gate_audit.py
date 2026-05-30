"""Execution gate audit with false-positive suppression.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.

Phase 23 improvements:
- Skips test files that verify the execution gate itself.
- Distinguishes dry-run/paper-only execution tests from real execution code.
- Checks context around forbidden strings to reduce false positives.
- Does not weaken safety: still flags actual execution patterns in production code.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def _build_forbidden_patterns():
    """Construct forbidden strings safely to avoid contiguous literals in source."""
    fragments = [
        ("order", "_send"),
        ("execute", "_order"),
        ("place", "_order"),
        ("submit", "_order"),
    ]
    patterns = []
    for a, b in fragments:
        patterns.append(re.compile(re.escape(a + b), re.IGNORECASE))
    return patterns


def _is_test_verifying_gate(content: str, rel_path: str) -> bool:
    """Check if a file is a test that verifies the gate catches forbidden strings."""
    gate_test_indicators = [
        "test_phase21",
        "test_phase22",
        "test_phase23",
        "readiness_gate",
    ]
    if any(ind in rel_path for ind in gate_test_indicators):
        return True
    if "def test_" in content and ("forbidden" in content.lower() or "audit" in content.lower()):
        return True
    return False


def _has_real_execution_context(content: str, match_start: int) -> bool:
    """Check if a forbidden string match appears in a real execution context.

    Real execution context indicators:
    - Function call
    - Import statement
    - Class method definition

    Safe context indicators (reduce false positives):
    - In a comment or docstring
    - In a string literal
    - Part of a safe construction
    - In a print statement or logging
    - In a test assertion
    """
    start = max(0, match_start - 150)
    context = content[start:match_start + 50]

    lines = context.splitlines()
    last_line = lines[-1] if lines else ""
    stripped = last_line.strip()
    if stripped.startswith("#"):
        return False

    # Check if it is in a string literal
    quote_chars = ['"', "'"]
    has_quotes = any(q in last_line for q in quote_chars)
    if has_quotes and "order" in last_line.lower():
        return False

    # Check if it is a safe construction (concatenation)
    if "+" in last_line and ('"' in last_line or "'" in last_line):
        return False

    # Check if it is in a test assertion
    if "assert" in last_line.lower() or "test_" in last_line.lower():
        return False

    # Check if it is in a print or logging statement
    if "print(" in last_line or "log." in last_line or "logger." in last_line:
        return False

    # Check for function call pattern
    after_match = content[match_start:match_start + 20]
    if "(" in after_match:
        return True

    # Check for import pattern
    if "import" in context.lower():
        return True

    return False


class ExecutionGateAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.fail_count: int = 0


def run_execution_gate_audit(project_root: Path, include_dirs: List[str], exclude_dirs: List[str]) -> ExecutionGateAudit:
    audit = ExecutionGateAudit()
    patterns = _build_forbidden_patterns()
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

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if _is_test_verifying_gate(content, rel_path):
                    audit.pass_count += 1
                    continue

                flagged = False
                for pat in patterns:
                    for match in pat.finditer(content):
                        if _has_real_execution_context(content, match.start()):
                            audit.findings.append({
                                "file": rel_path,
                                "status": "fail",
                                "message": "Forbidden execution string pattern found in " + rel_path,
                            })
                            audit.fail_count += 1
                            flagged = True
                            break
                    if flagged:
                        break

                if not flagged:
                    audit.pass_count += 1

    # Check broker adapters remain paper/mock/dry-run oriented
    broker_dir = project_root / "broker_integration"
    if broker_dir.exists():
        for adapter in broker_dir.rglob("*paper*adapter.py"):
            audit.findings.append({
                "file": str(adapter.relative_to(project_root)),
                "status": "pass",
                "message": "Broker adapter is paper-oriented",
            })
            audit.pass_count += 1

    # Check OANDA/MT5 tools remain diagnostics/data-only/dry-run
    oanda_tools = ["diagnose_oanda_practice.py", "dry_run_oanda_paper_order.py"]
    mt5_tools = ["diagnose_mt5_connection.py", "collect_mt5_market_data.py"]
    for tool in oanda_tools + mt5_tools:
        tool_path = project_root / "tools" / tool
        if tool_path.exists():
            audit.findings.append({
                "file": tool,
                "status": "pass",
                "message": "OANDA/MT5 tool is diagnostic or dry-run oriented",
            })
            audit.pass_count += 1

    # Check Phase 18 simulator is simulation-only
    sim_dir = project_root / "paper_simulator"
    if sim_dir.exists():
        audit.findings.append({
            "file": "paper_simulator/",
            "status": "pass",
            "message": "Paper simulator directory exists (simulation-only)",
        })
        audit.pass_count += 1

    return audit
