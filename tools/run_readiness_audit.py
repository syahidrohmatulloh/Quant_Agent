#!/usr/bin/env python3
"""CLI: run full readiness audit.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This readiness gate does not approve or enable live trading.
No broker calls. No live network. No credential input prompts.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from readiness_gate.readiness_config import load_readiness_config, validate_readiness_config
from readiness_gate.source_inventory import build_source_inventory
from readiness_gate.safety_audit import run_safety_audit
from readiness_gate.credential_audit import run_credential_audit
from readiness_gate.execution_gate_audit import run_execution_gate_audit
from readiness_gate.risk_control_audit import run_risk_control_audit
from readiness_gate.config_audit import run_config_audit
from readiness_gate.output_hygiene_audit import run_output_hygiene_audit
from readiness_gate.test_status_audit import run_test_status_audit
from readiness_gate.readiness_score import compute_readiness_score
from readiness_gate.readiness_report import generate_readiness_report
from readiness_gate.dashboard_export import export_dashboard, write_dashboard_json
from readiness_gate.readiness_log import append_readiness_log


def main():
    parser = argparse.ArgumentParser(description="Run full readiness audit")
    parser.add_argument("--config", required=True, help="Path to readiness config JSON")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This readiness gate does not approve or enable live trading.")
    print("No broker calls. No live network. No credential input prompts.")
    print("No actual email send. No actual Telegram send.")
    print("No background service installed. No cron installed automatically.")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FAIL: Config not found: {config_path}")
        sys.exit(1)

    config = load_readiness_config(config_path)
    issues = validate_readiness_config(config, allow_missing=args.allow_missing)
    if issues:
        for i in issues:
            print(f"CONFIG ISSUE: {i}")

    project_root = Path(config.project_root).resolve()

    inventory = build_source_inventory(project_root, config.include_dirs, config.exclude_dirs)
    safety = run_safety_audit(project_root, config.audit_rules)
    credential = run_credential_audit(project_root, config.include_dirs, config.exclude_dirs)
    execution = run_execution_gate_audit(project_root, config.include_dirs, config.exclude_dirs)
    risk = run_risk_control_audit(project_root, config.audit_rules)
    cfg_audit = run_config_audit(project_root, allow_missing=args.allow_missing)
    hygiene = run_output_hygiene_audit(project_root)
    tests = run_test_status_audit(project_root, run_tests=args.run_tests)

    total_items = max(1, inventory.total_files)
    source_pass = inventory.generated_output_files == 0 and inventory.backup_temp_cache_files == 0

    score = compute_readiness_score(
        source_inventory_pass=source_pass,
        safety_pass_rate=safety.pass_count / max(1, safety.pass_count + getattr(safety, "warning_count", len(getattr(safety, "warnings", []))) + safety.fail_count),
        credential_pass_rate=credential.pass_count / max(1, credential.pass_count + getattr(credential, "warning_count", len(getattr(credential, "warnings", []))) + credential.fail_count),
        execution_gate_pass_rate=execution.pass_count / max(1, execution.pass_count + execution.fail_count),
        risk_control_pass_rate=risk.pass_count / max(1, risk.pass_count + getattr(risk, "warning_count", len(getattr(risk, "warnings", []))) + risk.fail_count),
        config_pass_rate=cfg_audit.pass_count / max(1, cfg_audit.pass_count + getattr(cfg_audit, "warning_count", len(getattr(cfg_audit, "warnings", []))) + cfg_audit.fail_count),
        output_hygiene_warnings=getattr(hygiene, "warning_count", len(getattr(hygiene, "warnings", []))),
        test_status_pass=tests.pass_count > 0 or not args.run_tests,
    )

    report = generate_readiness_report(
        project_root, score, inventory, safety, credential, execution, risk, cfg_audit, hygiene, tests
    )

    # Write reports
    report_md_path = project_root / config.outputs.get("readiness_report_md", "reports/readiness_gate/readiness_report.md")
    report_json_path = project_root / config.outputs.get("readiness_report_json", "reports/readiness_gate/readiness_report.json")
    dashboard_path = project_root / config.outputs.get("dashboard_json", "reports/dashboard/readiness_gate/latest.json")
    log_path = project_root / config.outputs.get("readiness_log", "reports/readiness_gate/readiness_log.jsonl")

    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(report.markdown, encoding="utf-8")
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_json_path, "w", encoding="utf-8") as f:
        import json
        json.dump(report.json_data, f, indent=2)

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
        recommendations=report.json_data.get("recommendations", []),
        warnings=inventory.warnings + [f["message"] for f in hygiene.findings if f.get("status") == "warning"],
        errors=[f["message"] for f in top_findings if f.get("status") == "fail"],
    )
    write_dashboard_json(dashboard, dashboard_path)
    append_readiness_log(log_path, score, critical_count, warning_count)

    print(f"Readiness score: {score.score}/100 (Grade {score.grade}) — {score.status}")
    print(f"Reports written to:")
    print(f"  {report_md_path}")
    print(f"  {report_json_path}")
    print(f"  {dashboard_path}")
    print(f"  {log_path}")

    if score.status == "NOT_READY":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
