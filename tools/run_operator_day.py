#!/usr/bin/env python3
"""CLI: One-command operator day flow for local MVP.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
This tool does not approve or enable live trading.
No broker calls. No live network. No credential input prompts.
No actual email send. No actual Telegram send.
No background service installed. No cron installed automatically.

Orchestrates existing safe local tools:
- validate local app config using existing validation logic
- initialize local app dirs using existing safe local app logic
- run local app workflow using existing workflow logic
- generate or summarize daily briefing using existing safe text/report generation
- run readiness audit using existing CLI tool where possible
- collect health bundle using existing health logic
- build operator status summary

Example:
    python3 tools/run_operator_day.py \
        --config examples/local_app_config.example.json \
        --allow-missing
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
import subprocess
import traceback
from datetime import datetime, timezone
from typing import Any, Dict

from local_app.app_config import load_config, validate_config
from local_app.directory_manager import create_directories
from local_app.workflow_launcher import run_workflow
from local_app.health_bundle import collect_health
from local_app.operator_status import build_operator_status, render_operator_summary


def _print_disclaimer():
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("This tool does not approve or enable live trading.")
    print("No broker calls. No live network. No credential input prompts.")
    print("No actual email send. No actual Telegram send.")
    print("No background service installed. No cron installed automatically.")
    print("")


def _run_readiness_audit_step(project_root: Path, allow_missing: bool) -> Dict[str, Any]:
    """Try to run readiness audit using existing CLI tool."""
    result = {
        "step": "readiness_audit",
        "status": "skipped",
        "message": "Readiness config not found or audit skipped.",
    }
    readiness_cfg_path = project_root / "examples" / "readiness_gate_config.example.json"
    if not readiness_cfg_path.exists():
        result["message"] = f"Readiness config not found: {readiness_cfg_path}"
        return result

    cmd = [
        sys.executable,
        str(project_root / "tools" / "run_readiness_audit.py"),
        "--config", str(readiness_cfg_path),
    ]
    if allow_missing:
        cmd.append("--allow-missing")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode == 0:
            result["status"] = "success"
            # Try to extract score from stdout
            for line in proc.stdout.splitlines():
                if "Readiness score:" in line:
                    result["message"] = line.strip()
                    break
            else:
                result["message"] = "Readiness audit completed successfully."
        else:
            result["status"] = "warning" if allow_missing else "failed"
            result["message"] = f"Readiness audit exited {proc.returncode}."
            if proc.stderr:
                result["message"] += f" stderr: {proc.stderr[:200]}"
    except subprocess.TimeoutExpired:
        result["status"] = "warning" if allow_missing else "failed"
        result["message"] = "Readiness audit timed out."
    except Exception as e:
        result["status"] = "warning" if allow_missing else "failed"
        result["message"] = f"Readiness audit error: {e}"
        if not allow_missing:
            traceback.print_exc()

    return result


def main():
    parser = argparse.ArgumentParser(description="Run one-command operator day flow")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional artifacts")
    args = parser.parse_args()

    _print_disclaimer()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"BLOCKED: Config file not found: {config_path}")
        sys.exit(1)

    # Load config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"BLOCKED: Could not load config: {e}")
        sys.exit(1)

    # Validate config
    print("[1/6] Validating local app config...")
    validation = validate_config(config, allow_missing=args.allow_missing)
    if not validation["valid"]:
        print("BLOCKED: Config validation failed.")
        for err in validation["errors"]:
            print(f"  ERROR: {err}")
        sys.exit(1)
    for warn in validation.get("warnings", []):
        print(f"  WARNING: {warn}")
    print("  OK: Config valid and safe.")
    print("")

    project_root = PROJECT_ROOT

    # Init directories
    print("[2/6] Initializing local directories...")
    dir_result = create_directories(config, project_root)
    if not dir_result["success"]:
        print("BLOCKED: Directory initialization failed.")
        for err in dir_result.get("errors", []):
            print(f"  ERROR: {err}")
        sys.exit(1)
    for created in dir_result.get("created", []):
        print(f"  Created: {created}")
    print("  OK: Directories ready.")
    print("")

    # Run workflow
    print("[3/6] Running local app workflow...")
    workflow_summary = run_workflow(config, project_root, allow_missing=args.allow_missing)
    print(f"  Workflow status: {workflow_summary.get('overall_status', 'unknown')}")
    for step in workflow_summary.get("steps", []):
        print(f"    {step['step']}: {step['status']}")
    print("  OK: Workflow completed.")
    print("")

    # Collect health
    print("[4/6] Collecting health bundle...")
    try:
        health = collect_health(config, project_root, allow_missing=args.allow_missing)
        print(f"  Health overall: {health.get('overall', 'unknown')}")
        print("  OK: Health bundle collected.")
    except Exception as e:
        print(f"  WARNING: Health bundle failed: {e}")
    print("")

    # Readiness audit
    print("[5/6] Running readiness audit...")
    readiness_result = _run_readiness_audit_step(project_root, allow_missing=args.allow_missing)
    print(f"  Readiness audit: {readiness_result['status']} — {readiness_result['message']}")
    if readiness_result["status"] == "failed":
        print("  WARNING: Readiness audit failed but continuing.")
    print("  OK: Readiness step complete.")
    print("")

    # Build operator status
    print("[6/6] Building operator status summary...")
    status = build_operator_status(config, project_root, config_path=config_path, allow_missing=args.allow_missing)
    summary_text = render_operator_summary(status)
    print(summary_text)

    # Write operator status JSON for dashboard/tools
    reports_dir = config.get("directories", {}).get("reports", "reports")
    op_status_path = project_root / reports_dir / "local_app" / "operator_status.json"
    op_status_path.parent.mkdir(parents=True, exist_ok=True)
    with open(op_status_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "paper_only": status.paper_only,
            "data_only": status.data_only,
            "no_order_submission": status.no_order_submission,
            "config_path": status.config_path,
            "workflow_steps_completed": status.workflow_steps_completed,
            "workflow_steps_total": status.workflow_steps_total,
            "workflow_timestamp": status.workflow_timestamp,
            "readiness_score": status.readiness_score,
            "readiness_grade": status.readiness_grade,
            "readiness_status": status.readiness_status,
            "briefing_status": status.briefing_status,
            "dashboard_status": status.dashboard_status,
            "warnings": status.warnings,
            "blockers": status.blockers,
            "overall": status.overall,
            "next_safe_commands": status.next_safe_commands,
        }, f, indent=2)
    print(f"  Operator status written to: {op_status_path.relative_to(project_root)}")
    print("")

    if status.overall == "BLOCKED":
        print("BLOCKED: Operator day completed with blockers.")
        sys.exit(1)
    print("OK: Operator day completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
