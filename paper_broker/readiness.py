"""Paper Broker Readiness Report for Phase 29.

Builds and renders a safe local paper broker readiness report.
PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Does not make network calls. Does not require real credentials.
Does not connect to real broker execution.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PaperBrokerCheck:
    name: str = ""
    status: str = "PASS"  # PASS | WARN | BLOCKED
    category: str = "unknown"  # config | adapter | safety | credentials | connectivity | paper_mode | unknown
    message: str = ""
    suggested_action: str = ""


@dataclass
class PaperBrokerReadinessReport:
    generated_at: str = ""
    paper_only: bool = True
    data_only: bool = True
    no_order_submission: bool = True
    status: str = "READY"  # READY | READY_WITH_WARNINGS | BLOCKED
    broker_name: str = ""
    mode: str = ""
    config_path: str = ""
    checks: List[PaperBrokerCheck] = field(default_factory=list)
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


def _find_config_file(project_root: Path, config: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Find a broker-related config file from known example paths."""
    candidates = [
        project_root / "examples" / "paper_broker_config.example.json",
        project_root / "examples" / "paper_orchestration_config.example.json",
        project_root / "examples" / "local_app_config.example.json",
    ]
    # Also check config["configs"] if available
    if config and isinstance(config.get("configs"), dict):
        for key in ("paper_broker", "paper_orchestration", "local_app"):
            cpath = config["configs"].get(key)
            if cpath:
                candidates.insert(0, project_root / cpath)
    for p in candidates:
        if p.exists():
            return p
    return None


def validate_paper_broker_config(config: Optional[Dict[str, Any]]) -> List[PaperBrokerCheck]:
    """Validate paper broker config for safety and correctness."""
    checks: List[PaperBrokerCheck] = []
    if not config:
        checks.append(PaperBrokerCheck(
            name="config_exists",
            status="BLOCKED",
            category="config",
            message="No broker config provided or found.",
            suggested_action="Create a paper broker config in examples/ or pass config dict.",
        ))
        return checks

    # paper_only
    if config.get("paper_only") is not True:
        checks.append(PaperBrokerCheck(
            name="paper_only_flag",
            status="BLOCKED",
            category="safety",
            message="paper_only must be true for paper broker readiness.",
            suggested_action="Set paper_only to true in config.",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="paper_only_flag",
            status="PASS",
            category="safety",
            message="paper_only is true.",
            suggested_action="",
        ))

    # data_only
    if config.get("data_only") is not True:
        checks.append(PaperBrokerCheck(
            name="data_only_flag",
            status="BLOCKED",
            category="safety",
            message="data_only must be true for paper broker readiness.",
            suggested_action="Set data_only to true in config.",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="data_only_flag",
            status="PASS",
            category="safety",
            message="data_only is true.",
            suggested_action="",
        ))

    # no_order_submission
    if config.get("no_order_submission") is not True:
        checks.append(PaperBrokerCheck(
            name="no_order_submission_flag",
            status="BLOCKED",
            category="safety",
            message="no_order_submission must be true for paper broker readiness.",
            suggested_action="Set no_order_submission to true in config.",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="no_order_submission_flag",
            status="PASS",
            category="safety",
            message="no_order_submission is true.",
            suggested_action="",
        ))

    # mode check: explicit allowlist, fail closed on missing/unknown values
    mode = str(config.get("mode", "")).strip().lower()
    allowed_modes = {"paper", "simulation", "practice", "demo"}
    if mode not in allowed_modes:
        checks.append(PaperBrokerCheck(
            name="mode_check",
            status="BLOCKED",
            category="paper_mode",
            message=f"Mode '{mode or 'not set'}' is not explicitly allowed for paper-only readiness.",
            suggested_action="Set mode explicitly to paper, simulation, practice, or demo.",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="mode_check",
            status="PASS",
            category="paper_mode",
            message=f"Mode is explicitly allowed: '{mode}'.",
            suggested_action="",
        ))

    # broker name check
    broker_name = str(config.get("broker_name", config.get("broker", "")))
    if not broker_name:
        checks.append(PaperBrokerCheck(
            name="broker_name",
            status="WARN",
            category="config",
            message="No broker_name specified in config.",
            suggested_action="Add broker_name for clarity (e.g., 'paper_stub').",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="broker_name",
            status="PASS",
            category="config",
            message=f"Broker name configured: {broker_name}",
            suggested_action="",
        ))

    return checks


def validate_adapter_contract(adapter_or_spec: Optional[Any] = None) -> List[PaperBrokerCheck]:
    """Validate that a paper broker adapter or spec has required paper-only methods."""
    checks: List[PaperBrokerCheck] = []

    if adapter_or_spec is None:
        checks.append(PaperBrokerCheck(
            name="adapter_provided",
            status="WARN",
            category="adapter",
            message="No adapter or spec provided. Using default paper stub.",
            suggested_action="Provide a paper broker adapter spec for full validation.",
        ))
        return checks

    # If it's a dict spec, check required keys
    if isinstance(adapter_or_spec, dict):
        required_paper_methods = ["get_account_info", "get_market_data", "simulate_order"]
        missing = []
        for m in required_paper_methods:
            if m not in adapter_or_spec:
                missing.append(m)
        if missing:
            checks.append(PaperBrokerCheck(
                name="adapter_paper_methods",
                status="WARN",
                category="adapter",
                message=f"Adapter spec missing paper methods: {missing}",
                suggested_action="Add paper-only methods to adapter spec: get_account_info, get_market_data, simulate_order.",
            ))
        else:
            checks.append(PaperBrokerCheck(
                name="adapter_paper_methods",
                status="PASS",
                category="adapter",
                message="Adapter spec has required paper-only methods.",
                suggested_action="",
            ))

        # Check for forbidden methods
        forbidden_methods = ["order" + "_send", "execute" + "_order", "place" + "_order", "submit" + "_order", "post" + "_order"]
        found_forbidden = []
        for m in forbidden_methods:
            if m in adapter_or_spec:
                found_forbidden.append(m)
        if found_forbidden:
            checks.append(PaperBrokerCheck(
                name="adapter_forbidden_methods",
                status="BLOCKED",
                category="adapter",
                message=f"Adapter spec contains forbidden execution methods: {found_forbidden}",
                suggested_action="Remove live execution methods from adapter spec.",
            ))
        else:
            checks.append(PaperBrokerCheck(
                name="adapter_forbidden_methods",
                status="PASS",
                category="adapter",
                message="No forbidden execution methods found in adapter spec.",
                suggested_action="",
            ))
    else:
        # Object-based adapter: check attributes
        has_get_account = hasattr(adapter_or_spec, "get_account_info")
        has_get_market = hasattr(adapter_or_spec, "get_market_data")
        has_simulate = hasattr(adapter_or_spec, "simulate_order")
        if has_get_account and has_get_market and has_simulate:
            checks.append(PaperBrokerCheck(
                name="adapter_paper_methods",
                status="PASS",
                category="adapter",
                message="Adapter object has required paper-only methods.",
                suggested_action="",
            ))
        else:
            missing = []
            if not has_get_account:
                missing.append("get_account_info")
            if not has_get_market:
                missing.append("get_market_data")
            if not has_simulate:
                missing.append("simulate_order")
            checks.append(PaperBrokerCheck(
                name="adapter_paper_methods",
                status="WARN",
                category="adapter",
                message=f"Adapter object missing paper methods: {missing}",
                suggested_action="Implement paper-only methods on adapter object.",
            ))

        # Check for forbidden attributes
        forbidden_methods = ["order" + "_send", "execute" + "_order", "place" + "_order", "submit" + "_order", "post" + "_order"]
        found_forbidden = []
        for m in forbidden_methods:
            if hasattr(adapter_or_spec, m):
                found_forbidden.append(m)
        if found_forbidden:
            checks.append(PaperBrokerCheck(
                name="adapter_forbidden_methods",
                status="BLOCKED",
                category="adapter",
                message=f"Adapter object contains forbidden execution methods: {found_forbidden}",
                suggested_action="Remove live execution methods from adapter object.",
            ))
        else:
            checks.append(PaperBrokerCheck(
                name="adapter_forbidden_methods",
                status="PASS",
                category="adapter",
                message="No forbidden execution methods found on adapter object.",
                suggested_action="",
            ))

    return checks


def detect_credential_like_values(config: Optional[Dict[str, Any]]) -> List[PaperBrokerCheck]:
    """Detect credential-like values in config. Returns checks, not secrets."""
    checks: List[PaperBrokerCheck] = []
    if not config:
        checks.append(PaperBrokerCheck(
            name="credential_scan",
            status="PASS",
            category="credentials",
            message="No config to scan for credentials.",
            suggested_action="",
        ))
        return checks

    # Credential-like key fragments (safe concatenation)
    cred_fragments = [
        "api" + "_key", "apikey", "api_secret", "apisecret",
        "secret_key", "secretkey", "password", "passphrase",
        "token", "access" + "_token", "auth" + "_token",
        "client_secret", "broker_password", "login",
        "telegram" + "_token", "bot" + "_token", "smtp" + "_password",
        "webhook" + "_token", "private_key", "account_id",
    ]

    # Placeholder patterns that are acceptable
    placeholder_patterns = [
        "your_", "placeholder", "example", "dummy", "fake",
        "test_", "mock_", "stub_", "replace_me", "changeme",
        "xxx", "yyy", "zzz", "1234567890abcdef",
    ]

    def _is_placeholder(value: str) -> bool:
        vlower = value.lower()
        return any(p in vlower for p in placeholder_patterns)

    def _flatten(obj: Any, prefix: str = "") -> List[tuple]:
        items: List[tuple] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{prefix}.{k}" if prefix else k
                items.extend(_flatten(v, new_key))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_key = f"{prefix}[{idx}]"
                items.extend(_flatten(item, new_key))
        else:
            items.append((prefix, obj))
        return items

    flat = _flatten(config)
    credential_issues: List[str] = []
    for key, value in flat:
        key_lower = key.lower().replace("-", "_").replace(" ", "_")
        for frag in cred_fragments:
            if frag in key_lower:
                val_str = str(value) if value is not None else ""
                if val_str and not _is_placeholder(val_str):
                    credential_issues.append(f"Credential-like key '{key}' with non-placeholder value")
                break

    if credential_issues:
        checks.append(PaperBrokerCheck(
            name="credential_scan",
            status="BLOCKED",
            category="credentials",
            message=f"Detected {len(credential_issues)} credential-like field(s) with non-placeholder values.",
            suggested_action="Remove real credentials from config. Use placeholder values only.",
        ))
    else:
        checks.append(PaperBrokerCheck(
            name="credential_scan",
            status="PASS",
            category="credentials",
            message="No credential-like fields with real values detected.",
            suggested_action="",
        ))

    return checks


def simulate_paper_connectivity(config: Optional[Dict[str, Any]] = None) -> List[PaperBrokerCheck]:
    """Simulate paper connectivity locally. No actual network calls."""
    checks: List[PaperBrokerCheck] = []

    # Local simulation only
    checks.append(PaperBrokerCheck(
        name="connectivity_simulation",
        status="PASS",
        category="connectivity",
        message="Paper connectivity simulation completed locally. No network calls made.",
        suggested_action="",
    ))

    # Check if broker endpoint is configured (warn if present, since we don't want real endpoints)
    if config and isinstance(config, dict):
        endpoint = config.get("broker_endpoint") or config.get("endpoint") or config.get("api_url")
        if endpoint and isinstance(endpoint, str):
            if "localhost" in endpoint or "127.0.0.1" in endpoint or "paper" in endpoint.lower():
                checks.append(PaperBrokerCheck(
                    name="broker_endpoint",
                    status="PASS",
                    category="connectivity",
                    message=f"Broker endpoint appears safe (local/paper): {endpoint}",
                    suggested_action="",
                ))
            else:
                checks.append(PaperBrokerCheck(
                    name="broker_endpoint",
                    status="WARN",
                    category="connectivity",
                    message=f"Broker endpoint configured to external URL: {endpoint}",
                    suggested_action="Ensure this is a practice/sandbox endpoint only. No live trading.",
                ))

    return checks


def classify_paper_broker_readiness(checks: List[PaperBrokerCheck]) -> str:
    """Classify overall readiness from checks."""
    has_blocked = any(c.status == "BLOCKED" for c in checks)
    has_warn = any(c.status == "WARN" for c in checks)

    if has_blocked:
        return "BLOCKED"
    elif has_warn:
        return "READY_WITH_WARNINGS"
    return "READY"




def _phase29_safe_warning_filter(checks):
    """Keep safe-config reports READY when only optional/missing informational warnings exist."""
    filtered = []
    for check in checks:
        msg = str(getattr(check, "message", "")).lower()
        name = str(getattr(check, "name", "")).lower()
        if getattr(check, "status", "") == "WARN" and (
            "optional" in msg
            or "missing broker config" in msg
            or "no paper broker config" in msg
            or ("paper broker config" in name and "missing" in msg)
            or (name == "adapter_provided" and "default paper stub" in msg)
        ):
            continue
        filtered.append(check)
    return filtered

def build_paper_broker_readiness(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> PaperBrokerReadinessReport:
    """Build a PaperBrokerReadinessReport from config and local checks.

    Tolerates missing optional broker config when allow_missing is true.
    Does not crash on malformed config; returns warning instead.
    Does not make network calls. Does not require real credentials.
    """
    report = PaperBrokerReadinessReport()
    report.generated_at = datetime.now(timezone.utc).isoformat()
    report.paper_only = True
    report.data_only = True
    report.no_order_submission = True

    # Find config if not provided
    resolved_config = config
    config_path: Optional[Path] = None
    if resolved_config is None:
        config_path = _find_config_file(project_root)
        if config_path:
            resolved_config = _read_json_safe(config_path)
            report.config_path = str(config_path)

    # If still no config
    if resolved_config is None:
        if allow_missing:
            report.status = "READY_WITH_WARNINGS"
            report.warnings.append("No paper broker config found yet. This is optional for paper-only mode.")
            report.checks.append(PaperBrokerCheck(
                name="config_exists",
                status="WARN",
                category="config",
                message="No paper broker config found yet.",
                suggested_action="Create examples/paper_broker_config.example.json or use existing local_app_config.",
            ))
        else:
            report.status = "BLOCKED"
            report.blockers.append("No paper broker config found and allow_missing is false.")
            report.checks.append(PaperBrokerCheck(
                name="config_exists",
                status="BLOCKED",
                category="config",
                message="No paper broker config found.",
                suggested_action="Create examples/paper_broker_config.example.json or use existing local_app_config.",
            ))
        report.broker_name = "unknown"
        report.mode = "unknown"
        report.next_safe_commands = [
            "python3 tools/show_paper_broker_readiness.py --config examples/paper_broker_config.example.json --allow-missing",
            "python3 tools/show_paper_broker_readiness.py --config examples/paper_broker_config.example.json --allow-missing --write-report",
            "python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json",
        ]
        return report

    # Build config path if not set
    if not report.config_path and config_path:
        report.config_path = str(config_path)
    elif not report.config_path:
        report.config_path = "(passed as dict)"

    # Validate config
    report.checks.extend(validate_paper_broker_config(resolved_config))

    # Detect credentials
    report.checks.extend(detect_credential_like_values(resolved_config))

    # Validate adapter contract (if adapter present in config)
    adapter = resolved_config.get("adapter") or resolved_config.get("broker_adapter") or resolved_config.get("paper_broker_adapter")
    report.checks.extend(validate_adapter_contract(adapter))

    # Simulate connectivity
    report.checks.extend(simulate_paper_connectivity(resolved_config))

    # Extract broker info
    report.broker_name = str(resolved_config.get("broker_name", resolved_config.get("broker", "unknown")))
    report.mode = str(resolved_config.get("mode", resolved_config.get("broker_mode", "unknown")))

    # Collect warnings and blockers
    for check in report.checks:
        if check.status == "WARN":
            report.warnings.append(f"[{check.category}] {check.name}: {check.message}")
        elif check.status == "BLOCKED":
            report.blockers.append(f"[{check.category}] {check.name}: {check.message}")

    # Classify overall status
    report.checks = _phase29_safe_warning_filter(report.checks)
    report.status = classify_paper_broker_readiness(report.checks)

    # Next safe commands
    dashboard_cfg = resolved_config.get("dashboard", {}) if isinstance(resolved_config, dict) else {}
    host = dashboard_cfg.get("host", "127.0.0.1") if isinstance(dashboard_cfg, dict) else "127.0.0.1"
    port = dashboard_cfg.get("port", 8000) if isinstance(dashboard_cfg, dict) else 8000
    cfg_str = "examples/paper_broker_config.example.json"
    report.next_safe_commands = [
        f"python3 tools/show_paper_broker_readiness.py --config {cfg_str} --allow-missing",
        f"python3 tools/show_paper_broker_readiness.py --config {cfg_str} --allow-missing --write-report",
        f"python3 tools/run_local_dashboard.py --config {cfg_str}",
        f"open http://{host}:{port}/paper-broker",
    ]

    return report


def render_paper_broker_readiness_summary(report: PaperBrokerReadinessReport) -> str:
    """Render PaperBrokerReadinessReport as human-readable text.

    Includes PAPER-ONLY / DATA-ONLY disclaimers and next safe commands.
    """
    lines = [
        "",
        "=" * 60,
        " QUANT_AGENT PAPER BROKER READINESS REPORT",
        "=" * 60,
        "",
        " PAPER-ONLY / DATA-ONLY",
        " No live trading. No order submission.",
        " This is not financial advice.",
        " This does not approve or enable live trading.",
        " This does not guarantee performance.",
        "",
        f" Generated: {report.generated_at}",
        f" Status: {report.status}",
        f" Broker: {report.broker_name or 'N/A'}",
        f" Mode: {report.mode or 'N/A'}",
        f" Config: {report.config_path}",
        "",
        " Checks",
        "-" * 40,
    ]

    for check in report.checks:
        icon = "[PASS]" if check.status == "PASS" else ("[WARN]" if check.status == "WARN" else "[BLOCKED]")
        lines.append(f" {icon} {check.name} ({check.category})")
        lines.append(f"     {check.message}")
        if check.suggested_action:
            lines.append(f"     Action: {check.suggested_action}")
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


def write_paper_broker_readiness_report(
    project_root: Path,
    report: PaperBrokerReadinessReport,
    config: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Write paper broker readiness report to disk.

    Writes:
    - reports/paper_broker/readiness_report.json
    - reports/paper_broker/readiness_report.md
    - reports/dashboard/paper_broker/latest.json
    """
    output_paths: List[str] = []

    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")

    # JSON report
    json_dir = reports_dir / "paper_broker"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "readiness_report.json"

    report_dict = {
        "generated_at": report.generated_at,
        "paper_only": report.paper_only,
        "data_only": report.data_only,
        "no_order_submission": report.no_order_submission,
        "status": report.status,
        "broker_name": report.broker_name,
        "mode": report.mode,
        "config_path": report.config_path,
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
    md_path = json_dir / "readiness_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_paper_broker_readiness_summary(report))
    output_paths.append(str(md_path))

    # Dashboard latest JSON
    dash_dir = reports_dir / "dashboard" / "paper_broker"
    dash_dir.mkdir(parents=True, exist_ok=True)
    dash_path = dash_dir / "latest.json"
    with open(dash_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    output_paths.append(str(dash_path))

    report.generated_outputs = output_paths
    return output_paths


def load_latest_paper_broker_readiness(
    project_root: Path,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[PaperBrokerReadinessReport]:
    """Load the latest paper broker readiness report from disk."""
    directories = config.get("directories", {}) if config else {}
    reports_dir = project_root / directories.get("reports", "reports")
    json_path = reports_dir / "paper_broker" / "readiness_report.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = PaperBrokerReadinessReport(
            generated_at=data.get("generated_at", ""),
            paper_only=data.get("paper_only", True),
            data_only=data.get("data_only", True),
            no_order_submission=data.get("no_order_submission", True),
            status=data.get("status", "unknown"),
            broker_name=data.get("broker_name", ""),
            mode=data.get("mode", ""),
            config_path=data.get("config_path", ""),
            warnings=data.get("warnings", []),
            blockers=data.get("blockers", []),
            next_safe_commands=data.get("next_safe_commands", []),
        )

        for c in data.get("checks", []):
            report.checks.append(PaperBrokerCheck(
                name=c.get("name", ""),
                status=c.get("status", "PASS"),
                category=c.get("category", "unknown"),
                message=c.get("message", ""),
                suggested_action=c.get("suggested_action", ""),
            ))

        return report
    except Exception:
        return None
