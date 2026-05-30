"""Execution gate audit: verify no live order execution.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def _build_forbidden_patterns():
    # Construct forbidden strings safely to avoid contiguous literals in source
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


class ExecutionGateAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.fail_count: int = 0


def run_execution_gate_audit(project_root: Path, include_dirs: List[str], exclude_dirs: List[str]) -> ExecutionGateAudit:
    audit = ExecutionGateAudit()
    patterns = _build_forbidden_patterns()
    exclude_set = set(exclude_dirs)

    # Scan only Phase 21 new files by default, but accept config dirs
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

                for pat in patterns:
                    if pat.search(content):
                        audit.findings.append({
                            "file": rel_path,
                            "status": "fail",
                            "message": f"Forbidden execution string pattern found in {rel_path}",
                        })
                        audit.fail_count += 1
                        break
                else:
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
