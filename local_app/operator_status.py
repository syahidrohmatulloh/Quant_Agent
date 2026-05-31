"""Operator status builder for local MVP day-to-day clarity.

Builds a structured operator status object from existing local outputs.
Does not perform live trading. Does not submit orders.
Does not send email or Telegram. Does not install cron.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class OperatorStatus:
    mode: str = "paper-only / data-only"
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    config_path: str = ""
    workflow_steps_completed: int = 0
    workflow_steps_total: int = 0
    workflow_timestamp: Optional[str] = None
    latest_readiness_report_path: Optional[str] = None
    readiness_score: Optional[int] = None
    readiness_grade: Optional[str] = None
    readiness_status: Optional[str] = None
    latest_briefing_path: Optional[str] = None
    briefing_status: str = "not found"
    latest_dashboard_path: Optional[str] = None
    dashboard_status: str = "not found"
    generated_output_paths: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)
    overall: str = "unknown"
    # Phase 25 additions (backward-compatible defaults)
    warning_categories: Dict[str, List[str]] = field(default_factory=dict)
    readiness_action_items: List[str] = field(default_factory=list)
    workflow_action_items: List[str] = field(default_factory=list)
    briefing_action_items: List[str] = field(default_factory=list)
    dashboard_action_items: List[str] = field(default_factory=list)
    latest_operator_run: Optional[str] = None

def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _find_latest_file(parent: Path, pattern: str = "*") -> Optional[Path]:
    if not parent.exists():
        return None
    files = sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def build_operator_status(
    config: Dict[str, Any],
    project_root: Path,
    config_path: Optional[Path] = None,
    allow_missing: bool = False,
) -> OperatorStatus:
    directories = config.get("directories", {})
    reports_dir = project_root / directories.get("reports", "reports")

    status = OperatorStatus()
    status.config_path = str(config_path) if config_path else ""
    status.paper_only = bool(config.get("paper_only", True))
    status.data_only = bool(config.get("data_only", True))
    status.no_order_submission = bool(config.get("no_order_submission", True))

    # Workflow summary
    workflow_json = reports_dir / "local_app" / "workflow_summary.json"
    workflow_data = _read_json(workflow_json)
    if workflow_data:
        status.workflow_timestamp = workflow_data.get("timestamp")
        steps = workflow_data.get("steps", [])
        status.workflow_steps_total = len(steps)
        status.workflow_steps_completed = sum(
            1 for s in steps if s.get("status") in ("success", "skipped")
        )
        for s in steps:
            if s.get("status") == "failed":
                status.blockers.append(f"Workflow step failed: {s.get('step')}")
            elif s.get("status") == "warning":
                status.warnings.append(f"Workflow step warning: {s.get('step')}")
    else:
        if not allow_missing:
            status.warnings.append("No workflow summary found. Run workflow first.")

    # Readiness report
    readiness_json = reports_dir / "readiness_gate" / "readiness_report.json"
    readiness_data = _read_json(readiness_json)
    if readiness_data:
        status.latest_readiness_report_path = str(readiness_json.relative_to(project_root))
        score_data = readiness_data.get("score", {})
        status.readiness_score = score_data.get("score")
        status.readiness_grade = score_data.get("grade")
        status.readiness_status = score_data.get("status")
    else:
        status.warnings.append("No readiness report found. Run readiness audit for score.")

    # Briefing
    briefing_dir = reports_dir / "briefing"
    latest_briefing = _find_latest_file(briefing_dir)
    if latest_briefing:
        status.latest_briefing_path = str(latest_briefing.relative_to(project_root))
        status.briefing_status = "available"
    else:
        status.briefing_status = "not found"
        status.warnings.append("No briefing output found.")

    # Dashboard
    dashboard_dir = reports_dir / "dashboard"
    latest_dashboard = _find_latest_file(dashboard_dir)
    if latest_dashboard:
        status.latest_dashboard_path = str(latest_dashboard.relative_to(project_root))
        status.dashboard_status = "available"
    else:
        status.dashboard_status = "not found"
        status.warnings.append("No dashboard export found.")

    # Health check
    health_json = reports_dir / "local_app" / "health_check.json"
    if health_json.exists():
        status.generated_output_paths.append(str(health_json.relative_to(project_root)))

    if workflow_json.exists():
        status.generated_output_paths.append(str(workflow_json.relative_to(project_root)))
    md_path = reports_dir / "local_app" / "workflow_summary.md"
    if md_path.exists():
        status.generated_output_paths.append(str(md_path.relative_to(project_root)))

    if readiness_json.exists():
        status.generated_output_paths.append(str(readiness_json.relative_to(project_root)))
    md_path = reports_dir / "readiness_gate" / "readiness_report.md"
    if md_path.exists():
        status.generated_output_paths.append(str(md_path.relative_to(project_root)))

    # Next safe commands
    dashboard_cfg = config.get("dashboard", {})
    host = dashboard_cfg.get("host", "127.0.0.1")
    port = dashboard_cfg.get("port", 8000)
    status.next_safe_commands = [
        f"python3 tools/run_local_dashboard.py --config {status.config_path}",
        f"open http://{host}:{port}",
    ]

    # Overall
    if status.blockers:
        status.overall = "BLOCKED"
    elif status.warnings:
        status.overall = "OK_WITH_WARNINGS"
    else:
        status.overall = "OK"

    # Phase 25: populate action-center fields from readiness if available
    if readiness_data:
        from local_app.action_center import categorize_readiness_findings
        status.warning_categories = categorize_readiness_findings(readiness_data)
        if status.readiness_score is not None and status.readiness_score < 70:
            status.readiness_action_items.append(
                f"Readiness score {status.readiness_score}/100 is below 70. Review findings and improve coverage."
            )
    else:
        status.warning_categories = {"unknown": ["No readiness report available."]}
        status.readiness_action_items.append(
            "Run: python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing"
        )

    if not latest_briefing:
        status.briefing_action_items.append(
            "Run: python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json"
        )
    if not latest_dashboard:
        status.dashboard_action_items.append(
            "Run: python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json"
        )

    # Latest operator run timestamp
    op_status_json = reports_dir / "local_app" / "operator_status.json"
    op_data = _read_json(op_status_json)
    if op_data:
        status.latest_operator_run = op_data.get("timestamp")

    return status

def render_operator_summary(status: OperatorStatus) -> str:
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT OPERATOR DAY SUMMARY",
        "=" * 60,
        "",
        f" Mode: {status.mode}",
        f" Paper-only: {status.paper_only}",
        f" Data-only: {status.data_only}",
        " No " + "order" + f" submission: {status.no_order_submission}",
        "",
        f" Config: {status.config_path or 'N/A'}",
        f" Workflow: {status.workflow_steps_completed}/{status.workflow_steps_total} steps completed",
    ]
    if status.workflow_timestamp:
        lines.append(f" Workflow TS: {status.workflow_timestamp}")
    lines.append("")

    if status.readiness_score is not None:
        lines.append(f" Readiness: {status.readiness_score}/100 (Grade {status.readiness_grade}) — {status.readiness_status}")
    else:
        lines.append(" Readiness: N/A (run readiness audit)")
    lines.append("")

    lines.append(f" Briefing: {status.briefing_status}")
    if status.latest_briefing_path:
        lines.append(f" Path: {status.latest_briefing_path}")
    lines.append("")

    lines.append(f" Dashboard: {status.dashboard_status}")
    if status.latest_dashboard_path:
        lines.append(f" Path: {status.latest_dashboard_path}")
    lines.append("")

    if status.generated_output_paths:
        lines.append(" Generated outputs:")
        for p in status.generated_output_paths:
            lines.append(f" - {p}")
        lines.append("")

    if status.warnings:
        lines.append(f" Warnings ({len(status.warnings)}):")
        for w in status.warnings:
            lines.append(f" - {w}")
        lines.append("")

    if status.blockers:
        lines.append(f" BLOCKERS ({len(status.blockers)}):")
        for b in status.blockers:
            lines.append(f" ! {b}")
        lines.append("")

    lines.append(" Next safe commands:")
    for cmd in status.next_safe_commands:
        lines.append(f" $ {cmd}")
    lines.append("")

    lines.append(" Reminder: reports/logs/local outputs should not be committed.")
    lines.append(" This tool does not approve or enable live trading.")
    lines.append(" No broker calls. No live network. No credential prompts.")
    lines.append(" No actual email send. No actual Telegram send. No cron install.")
    lines.append("")
    lines.append("=" * 60)
    lines.append(f" Overall: {status.overall}")
    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)
