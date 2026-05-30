"""Readiness report generator.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .readiness_score import ReadinessScore
from .source_inventory import SourceInventory
from .safety_audit import SafetyAudit
from .credential_audit import CredentialAudit
from .execution_gate_audit import ExecutionGateAudit
from .risk_control_audit import RiskControlAudit
from .config_audit import ConfigAudit
from .output_hygiene_audit import OutputHygieneAudit
from .test_status_audit import ReadinessTestStatusAudit


class ReadinessReport:
    def __init__(self) -> None:
        self.markdown: str = ""
        self.json_data: Dict[str, Any] = {}


def generate_readiness_report(
    project_root: Path,
    score: ReadinessScore,
    inventory: SourceInventory,
    safety: SafetyAudit,
    credential: CredentialAudit,
    execution: ExecutionGateAudit,
    risk: RiskControlAudit,
    config: ConfigAudit,
    hygiene: OutputHygieneAudit,
    tests: ReadinessTestStatusAudit,
) -> ReadinessReport:
    report = ReadinessReport()
    now = datetime.now(timezone.utc).isoformat()

    critical_count = safety.fail_count + credential.fail_count + execution.fail_count + risk.fail_count + config.fail_count + tests.fail_count
    warning_count = getattr(safety, "warning_count", len(getattr(safety, "warnings", []))) + getattr(credential, "warning_count", len(getattr(credential, "warnings", []))) + getattr(risk, "warning_count", len(getattr(risk, "warnings", []))) + getattr(config, "warning_count", len(getattr(config, "warnings", []))) + getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", []))) + getattr(tests, "warning_count", len(getattr(tests, "warnings", [])))

    report.json_data = {
        "name": "quant_agent_mvp_readiness_gate",
        "generated_at": now,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "readiness_score": score.score,
        "grade": score.grade,
        "readiness_status": score.status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "source_inventory": {
            "total_files": inventory.total_files,
            "python_files": inventory.python_files,
            "tool_files": inventory.tool_files,
            "test_files": inventory.test_files,
            "example_config_files": inventory.example_config_files,
            "generated_output_files": inventory.generated_output_files,
            "backup_temp_cache_files": inventory.backup_temp_cache_files,
            "warnings": inventory.warnings,
        },
        "safety_audit": {
            "pass": safety.pass_count,
            "warning": getattr(safety, "warning_count", len(getattr(safety, "warnings", []))),
            "fail": safety.fail_count,
            "items": safety.items,
        },
        "credential_audit": {
            "pass": credential.pass_count,
            "warning": getattr(credential, "warning_count", len(getattr(credential, "warnings", []))),
            "fail": credential.fail_count,
            "findings": credential.findings,
        },
        "execution_gate_audit": {
            "pass": execution.pass_count,
            "fail": execution.fail_count,
            "findings": execution.findings,
        },
        "risk_control_audit": {
            "pass": risk.pass_count,
            "warning": getattr(risk, "warning_count", len(getattr(risk, "warnings", []))),
            "fail": risk.fail_count,
            "findings": risk.findings,
        },
        "config_audit": {
            "pass": config.pass_count,
            "warning": getattr(config, "warning_count", len(getattr(config, "warnings", []))),
            "fail": config.fail_count,
            "findings": config.findings,
        },
        "output_hygiene_audit": {
            "warning": getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", []))),
            "findings": hygiene.findings,
        },
        "test_status_audit": {
            "ran_tests": tests.ran_tests,
            "pass": tests.pass_count,
            "fail": tests.fail_count,
            "test_count": tests.test_count,
            "findings": tests.findings,
        },
        "recommendations": [
            "Remain paper-only at all times.",
            "Fix critical findings before any future live discussion.",
            "Keep credentials out of the repo.",
            "Review manually before any future live discussion.",
        ],
        "disclaimer": "This readiness gate does not approve or enable live trading. It is a paper-trading research safety audit only.",
    }

    md = f"""# Quant_Agent MVP Readiness Gate Report

**Generated at:** {now}

## Disclaimers

- **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission.
- **This readiness gate does not approve or enable live trading.** It is a paper-trading research safety audit only.

## Readiness Score

- **Score:** {score.score}/100
- **Grade:** {score.grade}
- **Status:** {score.status}

## Source Inventory Summary

- Total files: {inventory.total_files}
- Python files: {inventory.python_files}
- Tool files: {inventory.tool_files}
- Test files: {inventory.test_files}
- Example configs: {inventory.example_config_files}
- Generated outputs accidentally present: {inventory.generated_output_files}
- Backup/temp/cache files accidentally present: {inventory.backup_temp_cache_files}

## Safety Audit

- Pass: {safety.pass_count}
- Warning: {getattr(safety, "warning_count", len(getattr(safety, "warnings", [])))}
- Fail: {safety.fail_count}

## Credential Audit

- Pass: {credential.pass_count}
- Warning: {getattr(credential, "warning_count", len(getattr(credential, "warnings", [])))}
- Fail: {credential.fail_count}

## Execution Gate Audit

- Pass: {execution.pass_count}
- Fail: {execution.fail_count}

## Risk Control Audit

- Pass: {risk.pass_count}
- Warning: {getattr(risk, "warning_count", len(getattr(risk, "warnings", [])))}
- Fail: {risk.fail_count}

## Config Audit

- Pass: {config.pass_count}
- Warning: {getattr(config, "warning_count", len(getattr(config, "warnings", [])))}
- Fail: {config.fail_count}

## Output Hygiene Audit

- Warnings: {getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", [])))}

## Test Status Audit

- Ran tests: {tests.ran_tests}
- Pass: {tests.pass_count}
- Fail: {tests.fail_count}
- Test count (if detectable): {tests.test_count}

## Critical Findings

Total critical: {critical_count}

## Warnings

Total warnings: {warning_count}

## Recommendations

1. Remain paper-only.
2. Fix critical findings.
3. Keep credentials out of the repo.
4. Review manually before any future live discussion.

## Next Steps

- This system is intended for paper-trading research only.
- Do not enable live trading without a separate, explicit review.
"""

    report.markdown = md
    return report
