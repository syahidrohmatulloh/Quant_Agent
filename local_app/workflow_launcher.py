"""Workflow launcher for local app.

Runs selected local workflow steps safely.
Does not run broker network tools.
Does not call OANDA/MT5 live network tools.
Does not auto-send email/Telegram.
Collects step statuses and writes summary.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone


def _run_step(name: str, enabled: bool, project_root: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    if not enabled:
        return {"step": name, "status": "skipped", "message": "Disabled in workflow config"}

    # For Phase 20, we simulate step execution for paper_orchestration, paper_simulator, briefing
    # In a real scenario, these would invoke existing Python functions.
    # We create minimal placeholder outputs to show the workflow ran.

    if name == "paper_orchestration":
        # Placeholder: would call paper_orchestration.daily_runner
        return {"step": name, "status": "success", "message": "Paper orchestration step completed (placeholder)"}
    elif name == "paper_simulator":
        # Placeholder: would call paper_simulator.simulator_engine
        return {"step": name, "status": "success", "message": "Paper simulator step completed (placeholder)"}
    elif name == "briefing":
        # Placeholder: would call briefing.briefing_builder
        return {"step": name, "status": "success", "message": "Briefing generation step completed (placeholder)"}
    elif name == "research_analytics":
        return {"step": name, "status": "success", "message": "Research analytics step completed (placeholder)"}
    elif name == "data_import":
        return {"step": name, "status": "success", "message": "Data import step completed (placeholder)"}
    else:
        return {"step": name, "status": "warning", "message": f"Unknown step: {name}"}


def run_workflow(config: Dict[str, Any], project_root: Path, allow_missing: bool = False) -> Dict[str, Any]:
    workflow = config.get("workflow", {})
    continue_on_warning = workflow.get("continue_on_warning", True)
    steps: List[Dict[str, Any]] = []
    all_ok = True

    step_map = {
        "run_paper_orchestration": "paper_orchestration",
        "run_paper_simulator": "paper_simulator",
        "run_briefing": "briefing",
        "run_research_analytics": "research_analytics",
        "run_data_import": "data_import",
    }

    for flag_key, step_name in step_map.items():
        enabled = workflow.get(flag_key, False)
        result = _run_step(step_name, enabled, project_root, config)
        steps.append(result)
        if result["status"] == "failed":
            all_ok = False
            if not continue_on_warning:
                break
        elif result["status"] == "warning" and not continue_on_warning:
            all_ok = False
            break

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "steps": steps,
        "overall_status": "success" if all_ok else "failed",
    }

    # Write outputs
    reports_dir = project_root / config.get("directories", {}).get("reports", "reports") / "local_app"
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "workflow_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    md_path = reports_dir / "workflow_summary.md"
    md_lines = [
        "# Local App Workflow Summary",
        "",
        f"**Timestamp:** {summary['timestamp']}",
        f"**Status:** {summary['overall_status']}",
        "",
        "| Step | Status | Message |",
        "|------|--------|---------|",
    ]
    for s in steps:
        md_lines.append(f"| {s['step']} | {s['status']} | {s['message']} |")
    md_lines.append("")
    md_lines.append("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return summary
