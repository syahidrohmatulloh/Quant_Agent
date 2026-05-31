"""Paper Runtime Session Journal for Phase 27.

Builds and renders a local paper-runtime session journal from existing local outputs.
PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Does not make network calls. Does not require real market data.
Does not delete anything. Tolerates missing optional outputs.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PaperRuntimeSession:
    session_id: str = ""
    generated_at: str = ""
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    workflow_status: str = "unknown"
    workflow_steps: List[Dict[str, Any]] = field(default_factory=list)
    signal_summary: Dict[str, Any] = field(default_factory=dict)
    paper_decision_summary: Dict[str, Any] = field(default_factory=dict)
    portfolio_summary: Dict[str, Any] = field(default_factory=dict)
    pnl_summary: Dict[str, Any] = field(default_factory=dict)
    exposure_summary: Dict[str, Any] = field(default_factory=dict)
    risk_warnings: List[str] = field(default_factory=list)
    generated_outputs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)


@dataclass
class PaperRuntimeJournal:
    latest_session: Optional[PaperRuntimeSession] = None
    session_count: int = 0
    journal_path: str = ""
    latest_session_path: str = ""
    summary_path: str = ""
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


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


def _scan_dir_for_outputs(parent: Path, project_root: Path) -> List[str]:
    """Scan a directory for files and return relative paths."""
    outputs: List[str] = []
    if not parent.exists():
        return outputs
    for f in sorted(parent.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            try:
                outputs.append(str(f.relative_to(project_root)))
            except ValueError:
                outputs.append(str(f))
    return outputs


def _extract_workflow_status(workflow_data: Optional[Dict[str, Any]]) -> str:
    if not workflow_data:
        return "not_found"
    steps = workflow_data.get("steps", [])
    if not steps:
        return "no_steps"
    failed = sum(1 for s in steps if s.get("status") == "failed")
    warnings = sum(1 for s in steps if s.get("status") == "warning")
    completed = sum(1 for s in steps if s.get("status") in ("success", "skipped"))
    if failed > 0:
        return f"failed_{failed}"
    if warnings > 0:
        return f"warnings_{warnings}"
    if completed == len(steps):
        return "completed"
    return "in_progress"


def _extract_signal_summary(workflow_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract signal summary from workflow or dashboard data if available."""
    summary: Dict[str, Any] = {"status": "not_available", "signals": []}
    if not workflow_data:
        return summary
    # Try to find signal info in workflow summary
    signals = workflow_data.get("signals", [])
    if signals:
        summary["status"] = "available"
        summary["signals"] = signals
        summary["count"] = len(signals)
    return summary


def _extract_paper_decision_summary(
    workflow_data: Optional[Dict[str, Any]],
    operator_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extract paper decision summary from available outputs."""
    summary: Dict[str, Any] = {"status": "not_available", "decisions": []}
    # Check workflow for decisions
    if workflow_data:
        decisions = workflow_data.get("paper_decisions", [])
        if decisions:
            summary["status"] = "available"
            summary["decisions"] = decisions
            summary["count"] = len(decisions)
    # Check operator status for paper decisions
    if operator_data and summary["status"] == "not_available":
        decisions = operator_data.get("paper_decisions", [])
        if decisions:
            summary["status"] = "available"
            summary["decisions"] = decisions
            summary["count"] = len(decisions)
    return summary


def _extract_portfolio_summary(
    portfolio_dir: Path, project_root: Path
) -> Dict[str, Any]:
    """Extract portfolio summary from paper_portfolio reports."""
    summary: Dict[str, Any] = {"status": "not_available", "positions": []}
    if not portfolio_dir.exists():
        return summary
    latest = _find_latest_file(portfolio_dir, "*.json")
    if latest:
        data = _read_json_safe(latest)
        if data:
            summary["status"] = "available"
            summary["positions"] = data.get("positions", [])
            summary["position_count"] = len(data.get("positions", []))
            summary["source"] = str(latest.relative_to(project_root))
    return summary


def _extract_pnl_summary(
    simulator_dir: Path, project_root: Path
) -> Dict[str, Any]:
    """Extract PnL summary from paper_simulator reports."""
    summary: Dict[str, Any] = {"status": "not_available", "pnl": {}}
    if not simulator_dir.exists():
        return summary
    latest = _find_latest_file(simulator_dir, "*.json")
    if latest:
        data = _read_json_safe(latest)
        if data:
            summary["status"] = "available"
            summary["pnl"] = data.get("pnl", {})
            summary["source"] = str(latest.relative_to(project_root))
    return summary


def _extract_exposure_summary(
    portfolio_dir: Path, simulator_dir: Path, project_root: Path
) -> Dict[str, Any]:
    """Extract exposure summary from portfolio and simulator reports."""
    summary: Dict[str, Any] = {"status": "not_available", "exposure": {}}
    # Try portfolio first
    if portfolio_dir.exists():
        latest = _find_latest_file(portfolio_dir, "*.json")
        if latest:
            data = _read_json_safe(latest)
            if data:
                exposure = data.get("exposure", {})
                if exposure:
                    summary["status"] = "available"
                    summary["exposure"] = exposure
                    summary["source"] = str(latest.relative_to(project_root))
    # Try simulator as fallback
    if summary["status"] == "not_available" and simulator_dir.exists():
        latest = _find_latest_file(simulator_dir, "*.json")
        if latest:
            data = _read_json_safe(latest)
            if data:
                exposure = data.get("exposure", {})
                if exposure:
                    summary["status"] = "available"
                    summary["exposure"] = exposure
                    summary["source"] = str(latest.relative_to(project_root))
    return summary


def _collect_risk_warnings(
    workflow_data: Optional[Dict[str, Any]],
    readiness_data: Optional[Dict[str, Any]],
    operator_data: Optional[Dict[str, Any]],
) -> List[str]:
    """Collect risk warnings from various outputs."""
    warnings: List[str] = []
    # From workflow
    if workflow_data:
        for step in workflow_data.get("steps", []):
            if step.get("status") == "warning":
                warnings.append(f"Workflow warning: {step.get('step', 'unknown')}")
            if step.get("status") == "failed":
                warnings.append(f"Workflow failure: {step.get('step', 'unknown')}")
        wf_warnings = workflow_data.get("warnings", [])
        for w in wf_warnings:
            warnings.append(f"Workflow output warning: {w}")
    # From readiness
    if readiness_data:
        findings = readiness_data.get("findings", [])
        for finding in findings or []:
            msg = finding.get("message", "") if isinstance(finding, dict) else str(finding)
            sev = finding.get("severity", "warning") if isinstance(finding, dict) else "warning"
            if sev in ("warning", "error", "critical"):
                warnings.append(f"Readiness {sev}: {msg}")
        score_data = readiness_data.get("score", {})
        score = score_data.get("score") if isinstance(score_data, dict) else None
        if score is not None and score < 50:
            warnings.append(f"Readiness score critically low: {score}/100")
        elif score is not None and score < 70:
            warnings.append(f"Readiness score below 70: {score}/100")
    # From operator status
    if operator_data:
        op_warnings = operator_data.get("warnings", [])
        for w in op_warnings:
            warnings.append(f"Operator warning: {w}")
    return warnings


def _collect_generated_outputs(
    reports_dir: Path,
    project_root: Path,
    workflow_data: Optional[Dict[str, Any]],
) -> List[str]:
    """Collect list of generated output paths."""
    outputs: List[str] = []
    # Known report subdirectories
    subdirs = [
        "local_app",
        "paper_portfolio",
        "paper_simulator",
        "briefing",
        "dashboard",
        "readiness_gate",
        "research_analytics",
        "experiments",
        "strategy_lab",
    ]
    for subdir in subdirs:
        sub = reports_dir / subdir
        if sub.exists():
            for f in sorted(sub.rglob("*")):
                if f.is_file() and not f.name.startswith(".") and f.suffix in (".json", ".md", ".jsonl", ".txt"):
                    try:
                        outputs.append(str(f.relative_to(project_root)))
                    except ValueError:
                        outputs.append(str(f))
    # Deduplicate and sort
    seen = set()
    unique: List[str] = []
    for o in outputs:
        if o not in seen:
            seen.add(o)
            unique.append(o)
    return sorted(unique)


def build_paper_runtime_session(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> PaperRuntimeSession:
    """Build a PaperRuntimeSession from existing local outputs.

    Tolerates missing optional outputs when allow_missing is true.
    Does not crash on malformed JSON; returns warning instead.
    Does not delete anything. Does not make network calls.
    """
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")

    session = PaperRuntimeSession()
    session.session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    session.generated_at = datetime.now(timezone.utc).isoformat()
    session.paper_only = True
    session.data_only = True
    session.no_order_submission = True

    # Read optional existing outputs
    workflow_json = reports_dir / "local_app" / "workflow_summary.json"
    workflow_data = _read_json_safe(workflow_json)

    operator_json = reports_dir / "local_app" / "operator_status.json"
    operator_data = _read_json_safe(operator_json)

    readiness_json = reports_dir / "readiness_gate" / "readiness_report.json"
    readiness_data = _read_json_safe(readiness_json)

    portfolio_dir = reports_dir / "paper_portfolio"
    simulator_dir = reports_dir / "paper_simulator"

    # Workflow status
    if workflow_data:
        session.workflow_status = _extract_workflow_status(workflow_data)
        session.workflow_steps = workflow_data.get("steps", [])
    else:
        session.workflow_status = "not_found"
        if not allow_missing:
            session.warnings.append("No workflow summary found. Run workflow first.")

    # Signal summary
    session.signal_summary = _extract_signal_summary(workflow_data)
    if session.signal_summary["status"] == "not_available":
        if allow_missing:
            session.warnings.append("No signal summary available.")
        else:
            session.warnings.append("No signal summary available. Run signal generation first.")

    # Paper decision summary
    session.paper_decision_summary = _extract_paper_decision_summary(workflow_data, operator_data)
    if session.paper_decision_summary["status"] == "not_available":
        if allow_missing:
            session.warnings.append("No paper decision summary available.")

    # Portfolio summary
    session.portfolio_summary = _extract_portfolio_summary(portfolio_dir, project_root)
    if session.portfolio_summary["status"] == "not_available":
        if allow_missing:
            session.warnings.append("No portfolio summary available.")

    # PnL summary
    session.pnl_summary = _extract_pnl_summary(simulator_dir, project_root)
    if session.pnl_summary["status"] == "not_available":
        if allow_missing:
            session.warnings.append("No PnL summary available.")

    # Exposure summary
    session.exposure_summary = _extract_exposure_summary(portfolio_dir, simulator_dir, project_root)
    if session.exposure_summary["status"] == "not_available":
        if allow_missing:
            session.warnings.append("No exposure summary available.")

    # Risk warnings
    session.risk_warnings = _collect_risk_warnings(workflow_data, readiness_data, operator_data)

    # Generated outputs
    session.generated_outputs = _collect_generated_outputs(reports_dir, project_root, workflow_data)
    if not session.generated_outputs:
        session.warnings.append("No paper runtime outputs found yet.")

    # Blockers from readiness
    if readiness_data:
        score_data = readiness_data.get("score", {})
        score = score_data.get("score") if isinstance(score_data, dict) else None
        if score is not None and score < 50:
            session.blockers.append("Readiness score below 50. Review before proceeding.")
        findings = readiness_data.get("findings", [])
        for finding in findings or []:
            if isinstance(finding, dict) and finding.get("severity") == "critical":
                msg = finding.get("message", "")
                session.blockers.append(f"Critical readiness finding: {msg}")

    # Next safe commands
    dashboard_cfg = config.get("dashboard", {}) if config else {}
    host = dashboard_cfg.get("host", "127.0.0.1")
    port = dashboard_cfg.get("port", 8000)
    cfg_str = "examples/local_app_config.example.json"
    if config and config.get("name"):
        cfg_str = "examples/local_app_config.example.json"

    session.next_safe_commands = [
        f"python3 tools/show_paper_runtime_journal.py --config {cfg_str} --allow-missing",
        f"python3 tools/show_paper_runtime_journal.py --config {cfg_str} --allow-missing --write-journal",
        f"python3 tools/run_local_dashboard.py --config {cfg_str}",
        f"open http://{host}:{port}/paper-runtime",
    ]

    return session


def build_paper_runtime_journal(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> PaperRuntimeJournal:
    """Build a PaperRuntimeJournal from existing local outputs."""
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")
    paper_runtime_dir = reports_dir / "paper_runtime"

    journal = PaperRuntimeJournal()
    journal.journal_path = str(paper_runtime_dir / "session_journal.jsonl")
    journal.latest_session_path = str(paper_runtime_dir / "latest_session.json")
    journal.summary_path = str(paper_runtime_dir / "session_summary.md")

    # Count existing sessions in journal
    journal_file = paper_runtime_dir / "session_journal.jsonl"
    if journal_file.exists():
        try:
            with open(journal_file, "r", encoding="utf-8") as f:
                count = sum(1 for line in f if line.strip())
                journal.session_count = count
        except Exception:
            journal.warnings.append("Could not read existing session journal.")

    # Build latest session
    session = build_paper_runtime_session(project_root, config=config, allow_missing=allow_missing)
    journal.latest_session = session
    journal.warnings.extend(session.warnings)
    journal.blockers.extend(session.blockers)

    return journal


def write_paper_runtime_journal(
    project_root: Path,
    session: PaperRuntimeSession,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Write paper runtime journal outputs to local paths.

    Writes:
    - reports/paper_runtime/session_journal.jsonl (appends)
    - reports/paper_runtime/latest_session.json (overwrites)
    - reports/paper_runtime/session_summary.md (overwrites)

    Returns dict with written paths.
    """
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")
    paper_runtime_dir = reports_dir / "paper_runtime"
    paper_runtime_dir.mkdir(parents=True, exist_ok=True)

    written: Dict[str, str] = {}

    # Append to JSONL journal
    journal_path = paper_runtime_dir / "session_journal.jsonl"
    session_dict = asdict(session)
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(session_dict, ensure_ascii=False) + "\n")
    written["journal"] = str(journal_path.relative_to(project_root))

    # Overwrite latest_session.json
    latest_path = paper_runtime_dir / "latest_session.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(session_dict, f, indent=2, ensure_ascii=False)
    written["latest_session"] = str(latest_path.relative_to(project_root))

    # Overwrite session_summary.md
    summary_path = paper_runtime_dir / "session_summary.md"
    summary_text = render_paper_runtime_summary(session)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text)
    written["summary"] = str(summary_path.relative_to(project_root))

    return written


def render_paper_runtime_summary(session_or_journal) -> str:
    """Render a PaperRuntimeSession or PaperRuntimeJournal as human-readable text.

    Includes PAPER-ONLY / DATA-ONLY disclaimers and next safe commands.
    """
    if isinstance(session_or_journal, PaperRuntimeJournal):
        session = session_or_journal.latest_session
        if session is None:
            session = PaperRuntimeSession()
    else:
        session = session_or_journal

    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT PAPER RUNTIME SESSION SUMMARY",
        "=" * 60,
        "",
        " PAPER-ONLY / DATA-ONLY",
        " No live trading. No order submission.",
        " This is not financial advice.",
        " This does not approve or enable live trading.",
        " This does not guarantee performance.",
        "",
        f" Session ID: {session.session_id or 'N/A'}",
        f" Generated: {session.generated_at or 'N/A'}",
        f" Paper-only: {session.paper_only}",
        f" Data-only: {session.data_only}",
        " No " + "order" + f" submission: {session.no_order_submission}",
        "",
        " Workflow",
        "-" * 40,
        f" Status: {session.workflow_status}",
        f" Steps: {len(session.workflow_steps)}",
        "",
        " Signal Summary",
        "-" * 40,
        f" Status: {session.signal_summary.get('status', 'N/A')}",
    ]
    if session.signal_summary.get("count") is not None:
        lines.append(f" Count: {session.signal_summary['count']}")
    if session.signal_summary.get("signals"):
        for sig in session.signal_summary["signals"]:
            lines.append(f" - {sig}")
    lines.append("")

    lines.extend([
        " Paper Decision Summary",
        "-" * 40,
        f" Status: {session.paper_decision_summary.get('status', 'N/A')}",
    ])
    if session.paper_decision_summary.get("count") is not None:
        lines.append(f" Count: {session.paper_decision_summary['count']}")
    lines.append("")

    lines.extend([
        " Portfolio Summary",
        "-" * 40,
        f" Status: {session.portfolio_summary.get('status', 'N/A')}",
    ])
    if session.portfolio_summary.get("position_count") is not None:
        lines.append(f" Positions: {session.portfolio_summary['position_count']}")
    if session.portfolio_summary.get("source"):
        lines.append(f" Source: {session.portfolio_summary['source']}")
    lines.append("")

    lines.extend([
        " PnL Summary",
        "-" * 40,
        f" Status: {session.pnl_summary.get('status', 'N/A')}",
    ])
    if session.pnl_summary.get("source"):
        lines.append(f" Source: {session.pnl_summary['source']}")
    lines.append("")

    lines.extend([
        " Exposure Summary",
        "-" * 40,
        f" Status: {session.exposure_summary.get('status', 'N/A')}",
    ])
    if session.exposure_summary.get("source"):
        lines.append(f" Source: {session.exposure_summary['source']}")
    lines.append("")

    lines.extend([
        " Risk Warnings",
        "-" * 40,
    ])
    if session.risk_warnings:
        lines.append(f" Count: {len(session.risk_warnings)}")
        for w in session.risk_warnings:
            lines.append(f" - {w}")
    else:
        lines.append(" None")
    lines.append("")

    lines.extend([
        " Generated Outputs",
        "-" * 40,
    ])
    if session.generated_outputs:
        lines.append(f" Count: {len(session.generated_outputs)}")
        for p in session.generated_outputs[:20]:  # Limit display
            lines.append(f" - {p}")
        if len(session.generated_outputs) > 20:
            lines.append(f" ... and {len(session.generated_outputs) - 20} more")
    else:
        lines.append(" None yet")
    lines.append("")

    lines.extend([
        " Warnings",
        "-" * 40,
    ])
    if session.warnings:
        lines.append(f" Count: {len(session.warnings)}")
        for w in session.warnings:
            lines.append(f" - {w}")
    else:
        lines.append(" None")
    lines.append("")

    lines.extend([
        " Blockers",
        "-" * 40,
    ])
    if session.blockers:
        lines.append(f" Count: {len(session.blockers)}")
        for b in session.blockers:
            lines.append(f" ! {b}")
    else:
        lines.append(" None")
    lines.append("")

    lines.extend([
        " Next Safe Commands",
        "-" * 40,
    ])
    for cmd in session.next_safe_commands:
        lines.append(f" $ {cmd}")
    lines.append("")

    lines.extend([
        " Reminder: reports/logs/local outputs should not be committed.",
        " This tool does not approve or enable live trading.",
        " No broker calls. No live network. No credential prompts.",
        " No actual email send. No actual Telegram send. No cron install.",
        "",
        "=" * 60,
        "",
    ])

    return "\n".join(lines)


def load_latest_paper_runtime_session(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[PaperRuntimeSession]:
    """Load the latest paper runtime session from disk if available."""
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")
    latest_path = reports_dir / "paper_runtime" / "latest_session.json"
    data = _read_json_safe(latest_path)
    if not data:
        return None
    try:
        return PaperRuntimeSession(**data)
    except Exception:
        return None
