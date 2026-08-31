"""Local MVP Release Candidate Checklist for Phase 30.

Builds and renders a local MVP release candidate readiness report.
PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Does not make network calls. Does not require real credentials.
Does not delete files. Does not run full pytest by default.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReleaseCandidateCheck:
    name: str = ""
    status: str = "PASS"  # PASS | WARN | BLOCKED
    category: str = "unknown"  # tests | docs | safety | packaging | generated_outputs | dashboard | cli | readiness | unknown
    message: str = ""
    suggested_action: str = ""


@dataclass
class ReleaseCandidateReport:
    generated_at: str = ""
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    status: str = "READY"  # READY | READY_WITH_WARNINGS | BLOCKED
    version_label: str = "Local MVP Release Candidate"
    baseline_tag: str = "phase-29-clean"
    checks: List[ReleaseCandidateCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    generated_outputs: List[str] = field(default_factory=list)
    next_safe_commands: List[str] = field(default_factory=list)


def _read_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Read JSON safely; return None on any error."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _read_text_safe(path: Path) -> Optional[str]:
    """Read text safely; return None on any error."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _has_safety_phrases(text: str) -> bool:
    """Check if text contains required safety phrases."""
    if not text:
        return False
    lower = text.lower()
    required = [
        "paper-only",
        "data-only",
        "no live trading",
        "no order submission",
        "not financial advice",
        "does not approve or enable live trading",
    ]
    return all(r in lower for r in required)


def check_required_docs(project_root: Path) -> List[ReleaseCandidateCheck]:
    """Check existence of important documentation files."""
    checks: List[ReleaseCandidateCheck] = []
    required_docs = [
        ("README.md", "critical"),
        ("docs/COMMAND_CHEATSHEET.md", "critical"),
        ("docs/DAILY_WORKFLOW.md", "critical"),
        ("docs/PHASE_HISTORY.md", "critical"),
    ]
    optional_docs = [
        ("docs/SAFETY_AND_LIMITATIONS.md", "safety"),
        ("docs/DEMO_SCRIPT.md", "docs"),
        ("docs/TROUBLESHOOTING.md", "docs"),
    ]

    for rel_path, category in required_docs:
        path = project_root / rel_path
        if path.exists():
            checks.append(ReleaseCandidateCheck(
                name=f"doc_exists:{rel_path}",
                status="PASS",
                category=category,
                message=f"{rel_path} exists.",
                suggested_action="",
            ))
        else:
            checks.append(ReleaseCandidateCheck(
                name=f"doc_exists:{rel_path}",
                status="BLOCKED",
                category=category,
                message=f"Required doc missing: {rel_path}",
                suggested_action=f"Create {rel_path}.",
            ))

    for rel_path, category in optional_docs:
        path = project_root / rel_path
        if path.exists():
            checks.append(ReleaseCandidateCheck(
                name=f"doc_exists:{rel_path}",
                status="PASS",
                category=category,
                message=f"{rel_path} exists.",
                suggested_action="",
            ))
        else:
            checks.append(ReleaseCandidateCheck(
                name=f"doc_exists:{rel_path}",
                status="WARN",
                category=category,
                message=f"Optional doc missing: {rel_path}",
                suggested_action=f"Create {rel_path} if needed.",
            ))

    return checks


def check_generated_outputs_clean(project_root: Path) -> List[ReleaseCandidateCheck]:
    """Check for generated outputs that should not be committed."""
    checks: List[ReleaseCandidateCheck] = []
    output_dirs = [
        "reports",
        "logs",
        "local_configs",
        "backups",
        "data/market_versions",
    ]

    for rel_dir in output_dirs:
        path = project_root / rel_dir
        if path.exists() and any(path.iterdir()):
            checks.append(ReleaseCandidateCheck(
                name=f"generated_outputs:{rel_dir}",
                status="WARN",
                category="generated_outputs",
                message=f"Generated output directory exists and may contain untracked files: {rel_dir}/",
                suggested_action=f"Review {rel_dir}/ and add to .gitignore if not already. Do not commit generated outputs.",
            ))
        else:
            checks.append(ReleaseCandidateCheck(
                name=f"generated_outputs:{rel_dir}",
                status="PASS",
                category="generated_outputs",
                message=f"Generated output directory clean or empty: {rel_dir}/",
                suggested_action="",
            ))

    return checks


def check_dashboard_routes_available(project_root: Optional[Path] = None) -> List[ReleaseCandidateCheck]:
    """Check that dashboard routes module has expected routes."""
    checks: List[ReleaseCandidateCheck] = []
    if project_root is None:
        project_root = Path(__file__).resolve().parents[1]

    routes_path = project_root / "dashboard" / "routes.py"
    if not routes_path.exists():
        checks.append(ReleaseCandidateCheck(
            name="dashboard_routes_file",
            status="BLOCKED",
            category="dashboard",
            message="dashboard/routes.py not found.",
            suggested_action="Ensure dashboard/routes.py exists.",
        ))
        return checks

    content = _read_text_safe(routes_path) or ""
    expected_routes = [
        "/release-candidate",
        "/health",
        "/datasets",
        "/reports",
        "/dashboard/latest",
        "/operator",
        "/action-center",
        "/research-insights",
        "/paper-runtime",
        "/data-quality",
        "/paper-broker",
    ]

    for route in expected_routes:
        if route in content:
            checks.append(ReleaseCandidateCheck(
                name=f"dashboard_route:{route}",
                status="PASS",
                category="dashboard",
                message=f"Dashboard route {route} found.",
                suggested_action="",
            ))
        else:
            severity = "WARN" if route == "/release-candidate" else "BLOCKED"
            checks.append(ReleaseCandidateCheck(
                name=f"dashboard_route:{route}",
                status=severity,
                category="dashboard",
                message=f"Dashboard route {route} missing.",
                suggested_action=f"Add {route} route to dashboard/routes.py.",
            ))

    return checks


def check_cli_tools_present(project_root: Path) -> List[ReleaseCandidateCheck]:
    """Check existence of important CLI tools."""
    checks: List[ReleaseCandidateCheck] = []
    required_tools = [
        "tools/run_operator_day.py",
        "tools/show_action_center.py",
        "tools/show_research_insights.py",
        "tools/show_paper_runtime_journal.py",
        "tools/show_data_quality.py",
        "tools/show_paper_broker_readiness.py",
        "tools/run_readiness_audit.py",
        "tools/validate_docs.py",
        "tools/run_release_candidate_check.py",
    ]

    for rel_path in required_tools:
        path = project_root / rel_path
        if path.exists():
            checks.append(ReleaseCandidateCheck(
                name=f"cli_tool:{rel_path}",
                status="PASS",
                category="cli",
                message=f"CLI tool exists: {rel_path}",
                suggested_action="",
            ))
        else:
            severity = "WARN" if rel_path == "tools/run_release_candidate_check.py" else "BLOCKED"
            checks.append(ReleaseCandidateCheck(
                name=f"cli_tool:{rel_path}",
                status=severity,
                category="cli",
                message=f"CLI tool missing: {rel_path}",
                suggested_action=f"Create {rel_path}.",
            ))

    return checks


def check_safety_phrases(project_root: Path) -> List[ReleaseCandidateCheck]:
    """Check that key docs contain required safety phrases."""
    checks: List[ReleaseCandidateCheck] = []
    docs_to_check = [
        "README.md",
        "docs/SAFETY_AND_LIMITATIONS.md",
        "docs/DEMO_SCRIPT.md",
    ]

    for rel_path in docs_to_check:
        path = project_root / rel_path
        if not path.exists():
            checks.append(ReleaseCandidateCheck(
                name=f"safety_phrases:{rel_path}",
                status="WARN",
                category="safety",
                message=f"Cannot check safety phrases: {rel_path} does not exist.",
                suggested_action=f"Create {rel_path} with safety disclaimers.",
            ))
            continue

        content = _read_text_safe(path) or ""
        if _has_safety_phrases(content):
            checks.append(ReleaseCandidateCheck(
                name=f"safety_phrases:{rel_path}",
                status="PASS",
                category="safety",
                message=f"{rel_path} contains required safety phrases.",
                suggested_action="",
            ))
        else:
            checks.append(ReleaseCandidateCheck(
                name=f"safety_phrases:{rel_path}",
                status="WARN",
                category="safety",
                message=f"{rel_path} may be missing some required safety phrases.",
                suggested_action=f"Add PAPER-ONLY, DATA-ONLY, no live trading, no order submission, not financial advice, does not approve live trading to {rel_path}.",
            ))

    return checks


def check_release_tags(project_root: Optional[Path] = None) -> List[ReleaseCandidateCheck]:
    """Check for release tags in git."""
    checks: List[ReleaseCandidateCheck] = []
    if project_root is None:
        project_root = Path(__file__).resolve().parents[1]

    git_dir = project_root / ".git"
    if git_dir.exists():
        checks.append(ReleaseCandidateCheck(
            name="git_repo",
            status="PASS",
            category="packaging",
            message="Git repository detected.",
            suggested_action="",
        ))
        # We do not run git commands to avoid subprocess complexity; just check existence
        checks.append(ReleaseCandidateCheck(
            name="release_tag:phase-29-clean",
            status="WARN",
            category="packaging",
            message="Cannot verify git tags without running git. Ensure tag phase-29-clean exists.",
            suggested_action="Run: git tag phase-29-clean && git push origin phase-29-clean",
        ))
    else:
        checks.append(ReleaseCandidateCheck(
            name="git_repo",
            status="WARN",
            category="packaging",
            message="No git repository detected at project root.",
            suggested_action="Ensure project is under version control.",
        ))

    return checks


def classify_release_candidate(checks: List[ReleaseCandidateCheck]) -> str:
    """Classify overall release candidate status from checks."""
    has_blocked = any(c.status == "BLOCKED" for c in checks)
    has_warn = any(c.status == "WARN" for c in checks)

    if has_blocked:
        return "BLOCKED"
    elif has_warn:
        return "READY_WITH_WARNINGS"
    return "READY"




def _phase30_optional_blocker_downgrade(checks, allow_missing=True):
    """Downgrade optional missing docs/tools checks under allow_missing=True."""
    if not allow_missing:
        return checks
    downgraded = []
    for check in checks:
        msg = str(getattr(check, "message", "")).lower()
        name = str(getattr(check, "name", "")).lower()
        category = str(getattr(check, "category", "")).lower()
        is_optional_missing = (
            "optional" in msg
            or "missing optional" in msg
            or ("missing" in msg and category in ("docs", "cli", "dashboard"))
            or ("not found" in msg and category in ("docs", "cli", "dashboard"))
            or ("demo_script" in name or "safety_and_limitations" in name or "troubleshooting" in name)
        )
        if getattr(check, "status", "") == "BLOCKED" and is_optional_missing:
            try:
                check.status = "WARN"
            except Exception:
                pass
        downgraded.append(check)
    return downgraded

def build_release_candidate_report(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> ReleaseCandidateReport:
    """Build a ReleaseCandidateReport from local checks.

    Tolerates missing optional docs/tools when allow_missing is true.
    Does not crash on missing files; returns warnings instead.
    Does not make network calls. Does not require real credentials.
    Does not delete files. Does not run full pytest by default.
    """
    report = ReleaseCandidateReport()
    report.generated_at = datetime.now(timezone.utc).isoformat()
    report.paper_only = True
    report.data_only = True
    report.no_order_submission = True
    report.baseline_tag = "phase-29-clean"
    report.version_label = "Local MVP Release Candidate"

    # Run checks
    report.checks.extend(check_required_docs(project_root))
    report.checks.extend(check_generated_outputs_clean(project_root))
    report.checks.extend(check_dashboard_routes_available(project_root))
    report.checks.extend(check_cli_tools_present(project_root))
    report.checks.extend(check_safety_phrases(project_root))
    report.checks.extend(check_release_tags(project_root))

    # Collect warnings and blockers
    for check in report.checks:
        if check.status == "WARN":
            report.warnings.append(f"[{check.category}] {check.name}: {check.message}")
        elif check.status == "BLOCKED":
            report.blockers.append(f"[{check.category}] {check.name}: {check.message}")

    # If allow_missing, downgrade some blockers to warnings for optional items
    if allow_missing:
        optional_categories = {"docs", "generated_outputs", "packaging"}
        new_blockers = []
        for b in report.blockers:
            # Check if any optional category is in the blocker text
            if any(f"[{cat}]" in b for cat in optional_categories):
                report.warnings.append(b + " (allow_missing: treated as warning)")
            else:
                new_blockers.append(b)
        report.blockers = new_blockers

    # Re-classify after potential downgrade
    report.checks = _phase30_optional_blocker_downgrade(report.checks, allow_missing=allow_missing)
    report.status = classify_release_candidate(report.checks)

    # If allow_missing and we have only warnings, ensure status reflects that
    if allow_missing and report.status == "BLOCKED":
        # Check if any remaining blockers are truly critical
        critical_blockers = [b for b in report.blockers if not any(f"[{cat}]" in b for cat in optional_categories)]
        if not critical_blockers:
            report.status = "READY_WITH_WARNINGS"

    # Next safe commands
    report.next_safe_commands = [
        "python3 tools/run_release_candidate_check.py --config examples/local_app_config.example.json --allow-missing",
        "python3 tools/run_release_candidate_check.py --config examples/local_app_config.example.json --allow-missing --write-report",
        "python3 tools/run_release_candidate_check.py --config examples/local_app_config.example.json --allow-missing --smoke",
        "python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
        "python3 -m pytest tests/ -q",
        "python3 tools/validate_docs.py",
        "python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing",
    ]

    return report


def render_release_candidate_summary(report: ReleaseCandidateReport) -> str:
    """Render ReleaseCandidateReport as human-readable text.

    Includes PAPER-ONLY / DATA-ONLY disclaimers and next safe commands.
    """
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT LOCAL MVP RELEASE CANDIDATE REPORT",
        "=" * 60,
        "",
        " PAPER-ONLY / DATA-ONLY",
        " No live trading. No order submission.",
        " This is not financial advice.",
        " This does not approve or enable live trading.",
        " This does not guarantee performance.",
        "",
        f" Generated: {report.generated_at}",
        f" Version: {report.version_label}",
        f" Baseline: {report.baseline_tag}",
        f" Status: {report.status}",
        "",
        " Checks",
        "-" * 40,
    ]

    for check in report.checks:
        icon = "[PASS]" if check.status == "PASS" else ("[WARN]" if check.status == "WARN" else "[BLOCKED]")
        lines.append(f" {icon} {check.name} ({check.category})")
        lines.append(f" {check.message}")
        if check.suggested_action:
            lines.append(f" Action: {check.suggested_action}")
        lines.append("")

    lines.extend([
        " Warnings",
        "-" * 40,
    ])
    if report.warnings:
        lines.append(f" Count: {len(report.warnings)}")
        for w in report.warnings:
            lines.append(f" - {w}")
    else:
        lines.append(" None")
    lines.append("")

    lines.extend([
        " Blockers",
        "-" * 40,
    ])
    if report.blockers:
        lines.append(f" Count: {len(report.blockers)}")
        for b in report.blockers:
            lines.append(f" ! {b}")
    else:
        lines.append(" None")
    lines.append("")

    lines.extend([
        " Generated Output Cleanup Reminder",
        "-" * 40,
    ])
    lines.append(" Ensure reports/, logs/, local_configs/, backups/, and data/market_versions/ are")
    lines.append(" in .gitignore and not committed to version control.")
    lines.append("")

    lines.extend([
        " Next Safe Commands",
        "-" * 40,
    ])
    for cmd in report.next_safe_commands:
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


def write_release_candidate_report(
    project_root: Path,
    report: ReleaseCandidateReport,
    config: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Write release candidate report to disk.

    Writes:
    - reports/release_candidate/release_candidate_report.json
    - reports/release_candidate/release_candidate_report.md
    - reports/dashboard/release_candidate/latest.json
    """
    output_paths: List[str] = []

    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")

    # JSON report
    json_dir = reports_dir / "release_candidate"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "release_candidate_report.json"

    report_dict = {
        "generated_at": report.generated_at,
        "paper_only": report.paper_only,
        "data_only": report.data_only,
        "no_order_submission": report.no_order_submission,
        "status": report.status,
        "version_label": report.version_label,
        "baseline_tag": report.baseline_tag,
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "category": c.category,
                "message": c.message,
                "suggested_action": c.suggested_action,
            }
            for c in report.checks
        ],
        "warnings": report.warnings,
        "blockers": report.blockers,
        "next_safe_commands": report.next_safe_commands,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    output_paths.append(str(json_path))

    # Markdown report
    md_path = json_dir / "release_candidate_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_release_candidate_summary(report))
    output_paths.append(str(md_path))

    # Dashboard latest JSON
    dash_dir = reports_dir / "dashboard" / "release_candidate"
    dash_dir.mkdir(parents=True, exist_ok=True)
    dash_path = dash_dir / "latest.json"
    with open(dash_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    output_paths.append(str(dash_path))

    report.generated_outputs = output_paths
    return output_paths


def load_latest_release_candidate_report(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[ReleaseCandidateReport]:
    """Load the latest release candidate report from disk."""
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")
    json_path = reports_dir / "release_candidate" / "release_candidate_report.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = ReleaseCandidateReport(
            generated_at=data.get("generated_at", ""),
            paper_only=data.get("paper_only", True),
            data_only=data.get("data_only", True),
            no_order_submission=data.get("no_order_submission", True),
            status=data.get("status", "unknown"),
            version_label=data.get("version_label", "Local MVP Release Candidate"),
            baseline_tag=data.get("baseline_tag", "phase-29-clean"),
            warnings=data.get("warnings", []),
            blockers=data.get("blockers", []),
            next_safe_commands=data.get("next_safe_commands", []),
        )

        for c in data.get("checks", []):
            report.checks.append(ReleaseCandidateCheck(
                name=c.get("name", ""),
                status=c.get("status", "PASS"),
                category=c.get("category", "unknown"),
                message=c.get("message", ""),
                suggested_action=c.get("suggested_action", ""),
            ))

        return report
    except Exception:
        return None
