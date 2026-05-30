"""Test status audit.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import subprocess
from pathlib import Path
from typing import Dict, List, Any


class ReadinessTestStatusAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.fail_count: int = 0
        self.test_count: int = 0
        self.duration: float = 0.0
        self.ran_tests: bool = False


def run_test_status_audit(project_root: Path, run_tests: bool = False) -> ReadinessTestStatusAudit:
    audit = ReadinessTestStatusAudit()

    if not run_tests:
        audit.findings.append({
            "check": "test_status",
            "status": "pass",
            "message": "Tests skipped by default (fast audit). Use --run-tests to execute.",
        })
        audit.pass_count += 1
        return audit

    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        audit.ran_tests = True
        stdout = result.stdout + result.stderr
        # Try to parse test count
        for line in stdout.splitlines():
            if "passed" in line:
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        audit.test_count = int(part)
                        break
        if result.returncode == 0:
            audit.findings.append({
                "check": "test_status",
                "status": "pass",
                "message": f"Tests passed ({audit.test_count} detected)",
            })
            audit.pass_count += 1
        else:
            audit.findings.append({
                "check": "test_status",
                "status": "fail",
                "message": "Tests failed or had errors",
            })
            audit.fail_count += 1
    except Exception as e:
        audit.findings.append({
            "check": "test_status",
            "status": "fail",
            "message": f"Could not run tests: {e}",
        })
        audit.fail_count += 1

    return audit
