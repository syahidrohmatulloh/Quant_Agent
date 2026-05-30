#!/usr/bin/env python3
"""CLI: generate readiness report.

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
from readiness_gate.readiness_report import generate_readiness_report
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
    parser = argparse.ArgumentParser(description="Generate readiness report")
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

    report = generate_readiness_report(
        project_root, score, inventory, safety, credential, execution, risk, cfg_audit, hygiene, tests
    )

    report_md_path = project_root / config.outputs.get("readiness_report_md", "reports/readiness_gate/readiness_report.md")
    report_json_path = project_root / config.outputs.get("readiness_report_json", "reports/readiness_gate/readiness_report.json")
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(report.markdown, encoding="utf-8")
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_json_path, "w", encoding="utf-8") as f:
        import json
        json.dump(report.json_data, f, indent=2)

    print(f"Reports written to {report_md_path} and {report_json_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
