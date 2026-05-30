#!/usr/bin/env python3
"""CLI: export readiness dashboard JSON.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from readiness_gate.readiness_config import load_readiness_config
from readiness_gate.dashboard_export import export_dashboard, write_dashboard_json
from readiness_gate.readiness_score import compute_readiness_score
from readiness_gate.source_inventory import build_source_inventory
from readiness_gate.safety_audit import run_safety_audit
from readiness_gate.credential_audit import run_credential_audit
from readiness_gate.execution_gate_audit import run_execution_gate_audit
from readiness_gate.risk_control_audit import run_risk_control_audit
from readiness_gate.config_audit import run_config_audit
from readiness_gate.output_hygiene_audit import run_output_hygiene_audit
from readiness_gate.test_status_audit import run_test_status_audit


def main():
    parser = argparse.ArgumentParser(description="Export readiness dashboard JSON")
    parser.add_argument("--config", required=True, help="Path to readiness config JSON")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")

    config = load_readiness_config(Path(args.config))
    project_root = Path(config.project_root).resolve()

    inventory = build_source_inventory(project_root, config.include_dirs, config.exclude_dirs)
    safety = run_safety_audit(project_root, config.audit_rules)
    credential = run_credential_audit(project_root, config.include_dirs, config.exclude_dirs)
    execution = run_execution_gate_audit(project_root, config.include_dirs, config.exclude_dirs)
    risk = run_risk_control_audit(project_root, config.audit_rules)
    cfg_audit = run_config_audit(project_root, allow_missing=args.allow_missing)
    hygiene = run_output_hygiene_audit(project_root)
    tests = run_test_status_audit(project_root, run_tests=False)

    source_pass = inventory.generated_output_files == 0 and inventory.backup_temp_cache_files == 0
    score = compute_readiness_score(
        source_inventory_pass=source_pass,
        safety_pass_rate=safety.pass_count / max(1, safety.pass_count + getattr(safety, "warning_count", len(getattr(safety, "warnings", []))) + safety.fail_count),
        credential_pass_rate=credential.pass_count / max(1, credential.pass_count + getattr(credential, "warning_count", len(getattr(credential, "warnings", []))) + credential.fail_count),
        execution_gate_pass_rate=execution.pass_count / max(1, execution.pass_count + execution.fail_count),
        risk_control_pass_rate=risk.pass_count / max(1, risk.pass_count + getattr(risk, "warning_count", len(getattr(risk, "warnings", []))) + risk.fail_count),
        config_pass_rate=cfg_audit.pass_count / max(1, cfg_audit.pass_count + getattr(cfg_audit, "warning_count", len(getattr(cfg_audit, "warnings", []))) + cfg_audit.fail_count),
        output_hygiene_warnings=getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", []))),
        test_status_pass=True,
    )

    critical_count = safety.fail_count + credential.fail_count + execution.fail_count + risk.fail_count + cfg_audit.fail_count + tests.fail_count
    warning_count = getattr(safety, "warning_count", len(getattr(safety, "warnings", []))) + getattr(credential, "warning_count", len(getattr(credential, "warnings", []))) + getattr(risk, "warning_count", len(getattr(risk, "warnings", []))) + getattr(cfg_audit, "warning_count", len(getattr(cfg_audit, "warnings", []))) + getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", []))) + getattr(tests, "warning_count", len(getattr(tests, "warnings", [])))

    audit_summary = {
        "safety": {"pass": safety.pass_count, "warning": getattr(safety, "warning_count", len(getattr(safety, "warnings", []))), "fail": safety.fail_count},
        "credential": {"pass": credential.pass_count, "warning": getattr(credential, "warning_count", len(getattr(credential, "warnings", []))), "fail": credential.fail_count},
        "execution_gate": {"pass": execution.pass_count, "fail": execution.fail_count},
        "risk_control": {"pass": risk.pass_count, "warning": getattr(risk, "warning_count", len(getattr(risk, "warnings", []))), "fail": risk.fail_count},
        "config": {"pass": cfg_audit.pass_count, "warning": getattr(cfg_audit, "warning_count", len(getattr(cfg_audit, "warnings", []))), "fail": cfg_audit.fail_count},
        "output_hygiene": {"warning": getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", [])))},
        "test_status": {"pass": tests.pass_count, "fail": tests.fail_count, "ran": tests.ran_tests},
    }

    top_findings = []
    for finding in safety.items + credential.findings + execution.findings + risk.findings + cfg_audit.findings + hygiene.findings + tests.findings:
        if finding.get("status") in ("fail", "warning"):
            top_findings.append(finding)

    dashboard = export_dashboard(
        score=score,
        critical_count=critical_count,
        warning_count=warning_count,
        audit_summary=audit_summary,
        top_findings=top_findings[:10],
        recommendations=[
            "Remain paper-only at all times.",
            "Fix critical findings before any future live discussion.",
            "Keep credentials out of the repo.",
            "Review manually before any future live discussion.",
        ],
        warnings=inventory.warnings + [f["message"] for f in hygiene.findings if f.get("status") == "warning"],
        errors=[f["message"] for f in top_findings if f.get("status") == "fail"],
    )

    dashboard_path = project_root / config.outputs.get("dashboard_json", "reports/dashboard/readiness_gate/latest.json")
    write_dashboard_json(dashboard, dashboard_path)
    print(f"Dashboard exported to {dashboard_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
