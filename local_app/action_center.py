"""Action Center utilities for operator status and dashboard.

Pure, testable utilities for:
- categorizing warnings/findings
- summarizing action items
- producing dict output for CLI/dashboard

No network. No broker calls. No credentials.
No side effects except reading local JSON/text outputs when explicitly passed paths.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ActionCenter:
    """Structured action center for operator clarity."""
    mode: str = "paper-only / data-only"
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    latest_operator_run: Optional[str] = None
    warning_categories: Dict[str, List[str]] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    readiness_action_items: List[str] = field(default_factory=list)
    workflow_action_items: List[str] = field(default_factory=list)
    briefing_action_items: List[str] = field(default_factory=list)
    dashboard_action_items: List[str] = field(default_factory=list)
    paper_runtime_action_items: List[str] = field(default_factory=list)
    generated_outputs: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)
    overall: str = "unknown"
    readiness_score: Optional[int] = None
    readiness_grade: Optional[str] = None
    readiness_status: Optional[str] = None
    latest_paper_runtime_session_path: Optional[str] = None
    disclaimer: str = (
        "This does not approve or enable live trading. "
        "No broker calls. No live network. No credential prompts. "
        "No actual email send. No actual Telegram send. No cron install."
    )


def _read_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Read JSON safely; return None on any error."""
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


def categorize_readiness_findings(readiness_data: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Categorize readiness findings into stable categories.

    Returns dict with keys:
    - config
    - data
    - safety
    - tests
    - docs
    - unknown
    """
    categories: Dict[str, List[str]] = {
        "config": [],
        "data": [],
        "safety": [],
        "tests": [],
        "docs": [],
        "unknown": [],
    }
    if not readiness_data:
        categories["unknown"].append("No readiness report available.")
        return categories

    findings = readiness_data.get("findings", [])
    if not findings and readiness_data.get("score"):
        # If there are no explicit findings but score exists, assume OK
        return categories

    for finding in findings or []:
        msg = finding.get("message", "") if isinstance(finding, dict) else str(finding)
        severity = finding.get("severity", "warning") if isinstance(finding, dict) else "warning"
        label = f"[{severity.upper()}] {msg}"

        lowered = msg.lower()
        if any(k in lowered for k in ("config", "setting", "parameter", "json")):
            categories["config"].append(label)
        elif any(k in lowered for k in ("csv", "dataset", "market", "data", "import", "symbol")):
            categories["data"].append(label)
        elif any(k in lowered for k in ("safety", "paper", "live", "broker", "order", "credential", "token")):
            categories["safety"].append(label)
        elif any(k in lowered for k in ("test", "pytest", "coverage")):
            categories["tests"].append(label)
        elif any(k in lowered for k in ("doc", "readme", "markdown", "cheatsheet", "workflow")):
            categories["docs"].append(label)
        else:
            categories["unknown"].append(label)

    return categories


def build_operator_action_center(
    config: Dict[str, Any],
    project_root: Path,
    config_path: Optional[Path] = None,
    allow_missing: bool = False,
) -> ActionCenter:
    """Build an ActionCenter from existing local outputs.

    Tolerates missing optional outputs when allow_missing is true.
    Does not crash on malformed JSON; returns warning/action item instead.
    Does not delete anything. Does not make network calls.
    """
    directories = config.get("directories", {})
    reports_dir = project_root / directories.get("reports", "reports")

    ac = ActionCenter()
    ac.paper_only = bool(config.get("paper_only", True))
    ac.data_only = bool(config.get("data_only", True))
    ac.no_order_submission = bool(config.get("no_order_submission", True))

    # Latest operator run timestamp from operator_status.json if present
    op_status_json = reports_dir / "local_app" / "operator_status.json"
    op_status_data = _read_json_safe(op_status_json)
    if op_status_data:
        ac.latest_operator_run = op_status_data.get("timestamp")
        # Carry forward existing warnings/blockers if present
        ac.warnings.extend(op_status_data.get("warnings", []))
        ac.blockers.extend(op_status_data.get("blockers", []))

    # Workflow summary
    workflow_json = reports_dir / "local_app" / "workflow_summary.json"
    workflow_data = _read_json_safe(workflow_json)
    if workflow_data:
        steps = workflow_data.get("steps", [])
        for s in steps:
            status = s.get("status")
            step_name = s.get("step", "unknown")
            if status == "failed":
                ac.blockers.append(f"Workflow step failed: {step_name}")
                ac.workflow_action_items.append(f"Fix workflow step: {step_name}")
            elif status == "warning":
                ac.warnings.append(f"Workflow step warning: {step_name}")
                ac.workflow_action_items.append(f"Review workflow step: {step_name}")
    else:
        if not allow_missing:
            ac.warnings.append("No workflow summary found. Run workflow first.")
        ac.workflow_action_items.append("Run: python3 tools/run_local_app_workflow.py --config <config> --allow-missing")

    # Readiness report
    readiness_json = reports_dir / "readiness_gate" / "readiness_report.json"
    readiness_data = _read_json_safe(readiness_json)
    if readiness_data:
        score_data = readiness_data.get("score", {})
        ac.readiness_score = score_data.get("score")
        ac.readiness_grade = score_data.get("grade")
        ac.readiness_status = score_data.get("status")
        ac.warning_categories = categorize_readiness_findings(readiness_data)
        if ac.readiness_score is not None and ac.readiness_score < 70:
            ac.readiness_action_items.append(
                f"Readiness score {ac.readiness_score}/100 is below 70. Review findings and improve coverage."
            )
    else:
        ac.warnings.append("No readiness report found. Run readiness audit for score.")
        ac.readiness_action_items.append("Run: python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing")
        if "unknown" not in ac.warning_categories:
            ac.warning_categories["unknown"] = []
        ac.warning_categories["unknown"].append("No readiness report available.")

    # Briefing
    briefing_dir = reports_dir / "briefing"
    latest_briefing = _find_latest_file(briefing_dir)
    if latest_briefing:
        ac.generated_outputs.append(str(latest_briefing.relative_to(project_root)))
    else:
        ac.warnings.append("No briefing output found.")
        ac.briefing_action_items.append("Run: python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json")

    # Dashboard
    dashboard_dir = reports_dir / "dashboard"
    latest_dashboard = _find_latest_file(dashboard_dir)
    if latest_dashboard:
        ac.generated_outputs.append(str(latest_dashboard.relative_to(project_root)))
    else:
        ac.warnings.append("No dashboard export found.")
        ac.dashboard_action_items.append("Run: python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json")

    # Health check
    health_json = reports_dir / "local_app" / "health_check.json"
    if health_json.exists():
        ac.generated_outputs.append(str(health_json.relative_to(project_root)))

    if workflow_json.exists():
        ac.generated_outputs.append(str(workflow_json.relative_to(project_root)))
    md_path = reports_dir / "local_app" / "workflow_summary.md"
    if md_path.exists():
        ac.generated_outputs.append(str(md_path.relative_to(project_root)))

    if readiness_json.exists():
        ac.generated_outputs.append(str(readiness_json.relative_to(project_root)))
    md_path = reports_dir / "readiness_gate" / "readiness_report.md"
    if md_path.exists():
        ac.generated_outputs.append(str(md_path.relative_to(project_root)))

    # Paper runtime session
    paper_runtime_dir = reports_dir / "paper_runtime"
    latest_session_json = paper_runtime_dir / "latest_session.json"
    if latest_session_json.exists():
        ac.latest_paper_runtime_session_path = str(latest_session_json.relative_to(project_root))
        ac.generated_outputs.append(str(latest_session_json.relative_to(project_root)))
    else:
        ac.warnings.append("No paper runtime session found.")
        ac.paper_runtime_action_items.append(
            "Run: python3 tools/show_paper_runtime_journal.py --config examples/local_app_config.example.json --allow-missing --write-journal"
        )

    # Next safe commands
    dashboard_cfg = config.get("dashboard", {})
    host = dashboard_cfg.get("host", "127.0.0.1")
    port = dashboard_cfg.get("port", 8000)
    cfg_str = str(config_path) if config_path else "examples/local_app_config.example.json"
    ac.next_safe_commands = [
        f"python3 tools/run_operator_day.py --config {cfg_str} --allow-missing",
        f"python3 tools/show_local_app_status.py --config {cfg_str} --allow-missing",
        f"python3 tools/show_paper_runtime_journal.py --config {cfg_str} --allow-missing",
        f"python3 tools/show_paper_runtime_journal.py --config {cfg_str} --allow-missing --write-journal",
        f"python3 tools/run_local_dashboard.py --config {cfg_str}",
        f"open http://{host}:{port}",
    ]

    # Overall
    if ac.blockers:
        ac.overall = "BLOCKED"
    elif ac.warnings:
        ac.overall = "OK_WITH_WARNINGS"
    else:
        ac.overall = "OK"

    return ac


def render_action_center_summary(ac: ActionCenter) -> str:
    """Render ActionCenter as a human-readable CLI string."""
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT ACTION CENTER",
        "=" * 60,
        "",
        f" Mode: {ac.mode}",
        f" Paper-only: {ac.paper_only}",
        f" Data-only: {ac.data_only}",
        " No " + "order" + f" submission: {ac.no_order_submission}",
        "",
    ]

    if ac.latest_operator_run:
        lines.append(f" Latest operator run: {ac.latest_operator_run}")
        lines.append("")

    if ac.readiness_score is not None:
        lines.append(f" Readiness: {ac.readiness_score}/100 (Grade {ac.readiness_grade}) — {ac.readiness_status}")
    else:
        lines.append(" Readiness: N/A (run readiness audit)")
    lines.append("")

    lines.append(f" Critical blockers: {len(ac.blockers)}")
    lines.append(f" Warnings: {len(ac.warnings)}")
    lines.append("")

    if ac.warning_categories:
        lines.append(" Warning categories:")
        for cat, items in ac.warning_categories.items():
            if items:
                lines.append(f" [{cat.upper()}] {len(items)} item(s)")
                for item in items:
                    lines.append(f"   - {item}")
        lines.append("")

    if ac.blockers:
        lines.append(" BLOCKERS:")
        for b in ac.blockers:
            lines.append(f" ! {b}")
        lines.append("")

    if ac.warnings:
        lines.append(" WARNINGS:")
        for w in ac.warnings:
            lines.append(f" - {w}")
        lines.append("")

    if ac.readiness_action_items:
        lines.append(" Readiness action items:")
        for item in ac.readiness_action_items:
            lines.append(f" • {item}")
        lines.append("")

    if ac.workflow_action_items:
        lines.append(" Workflow action items:")
        for item in ac.workflow_action_items:
            lines.append(f" • {item}")
        lines.append("")

    if ac.briefing_action_items:
        lines.append(" Briefing action items:")
        for item in ac.briefing_action_items:
            lines.append(f" • {item}")
        lines.append("")

    if ac.dashboard_action_items:
        lines.append(" Dashboard action items:")
        for item in ac.dashboard_action_items:
            lines.append(f" • {item}")
        lines.append("")

    if ac.paper_runtime_action_items:
        lines.append(" Paper runtime action items:")
        for item in ac.paper_runtime_action_items:
            lines.append(f" • {item}")
        lines.append("")

    if ac.generated_outputs:
        lines.append(" Latest generated outputs:")
        for p in ac.generated_outputs:
            lines.append(f" - {p}")
        lines.append("")

    lines.append(" Next safe commands:")
    for cmd in ac.next_safe_commands:
        lines.append(f" $ {cmd}")
    lines.append("")

    lines.append(" Reminder: reports/logs/local outputs should not be committed.")
    lines.append(" This tool does not approve or enable live trading.")
    lines.append(" No broker calls. No live network. No credential prompts.")
    lines.append(" No actual email send. No actual Telegram send. No cron install.")
    lines.append("")
    lines.append("=" * 60)
    lines.append(f" Overall: {ac.overall}")
    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)
