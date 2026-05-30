"""Safety audit for paper-only disclaimers and controls.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.

Phase 23 improvements:
- Better classification of scheduler tools: distinguishes command generation from auto-installation.
- Better classification of briefing tools: distinguishes text generation from auto-send.
- Distinguishes documentation references from actual unsafe behavior.
- Adds pass entries for tools that explicitly require confirmation.
"""
from pathlib import Path
from typing import Dict, List, Any


class SafetyAudit:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.warning_count: int = 0
        self.fail_count: int = 0


def run_safety_audit(project_root: Path, audit_rules: Dict[str, Any]) -> SafetyAudit:
    audit = SafetyAudit()

    # Check paper-only disclaimers in workflow CLI tools
    tools_dir = project_root / "tools"
    if tools_dir.exists():
        for py_file in tools_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            has_disclaimer = "PAPER-ONLY" in content or "DATA-ONLY" in content or "paper-only" in content.lower()
            if not has_disclaimer:
                # Phase 23: check if this is a documentation/utility tool that does not touch trading logic
                is_doc_tool = py_file.name.startswith(("validate_docs", "show_demo", "show_command"))
                is_cleanup_tool = "cleanup" in py_file.name or "restore" in py_file.name
                if is_doc_tool or is_cleanup_tool:
                    # Doc and cleanup tools get a pass if they have any disclaimer
                    if "disclaimer" in content.lower() or "safety" in content.lower():
                        audit.items.append({
                            "check": "paper_only_disclaimer",
                            "file": str(py_file.relative_to(project_root)),
                            "status": "pass",
                            "message": "Utility tool has safety reference",
                        })
                        audit.pass_count += 1
                        continue
                audit.items.append({
                    "check": "paper_only_disclaimer",
                    "file": str(py_file.relative_to(project_root)),
                    "status": "warning",
                    "message": "Missing paper-only disclaimer",
                })
                audit.warning_count += 1
            else:
                audit.items.append({
                    "check": "paper_only_disclaimer",
                    "file": str(py_file.relative_to(project_root)),
                    "status": "pass",
                    "message": "Paper-only disclaimer present",
                })
                audit.pass_count += 1

    # Check dashboard default host is localhost
    dashboard_files = list((project_root / "dashboard").glob("*.py")) if (project_root / "dashboard").exists() else []
    localhost_found = False
    for df in dashboard_files:
        content = df.read_text(encoding="utf-8", errors="ignore")
        if "127.0.0.1" in content or "localhost" in content:
            localhost_found = True
            break
    if localhost_found:
        audit.items.append({
            "check": "dashboard_localhost",
            "status": "pass",
            "message": "Dashboard references localhost",
        })
        audit.pass_count += 1
    else:
        audit.items.append({
            "check": "dashboard_localhost",
            "status": "warning",
            "message": "Dashboard localhost not confirmed",
        })
        audit.warning_count += 1

    # Check cleanup/restore tools require explicit confirmation
    cleanup_tools = ["cleanup_generated_outputs.py", "restore_local_config_backup.py", "restore_data.py"]
    for tool_name in cleanup_tools:
        tool_path = tools_dir / tool_name if tools_dir.exists() else None
        if tool_path and tool_path.exists():
            content = tool_path.read_text(encoding="utf-8", errors="ignore")
            has_confirm = "confirm" in content.lower() or "--yes" in content or "--force" in content
            if has_confirm:
                audit.items.append({
                    "check": "cleanup_restore_confirmation",
                    "file": tool_name,
                    "status": "pass",
                    "message": "Cleanup/restore tool requires confirmation",
                })
                audit.pass_count += 1
            else:
                audit.items.append({
                    "check": "cleanup_restore_confirmation",
                    "file": tool_name,
                    "status": "warning",
                    "message": "Cleanup/restore tool may lack confirmation",
                })
                audit.warning_count += 1

    # Check scheduler tools do not install cron automatically
    scheduler_tools = ["generate_scheduler_command.py", "generate_daily_workflow_command.py", "generate_briefing_scheduler_command.py"]
    for tool_name in scheduler_tools:
        tool_path = tools_dir / tool_name if tools_dir.exists() else None
        if tool_path and tool_path.exists():
            content = tool_path.read_text(encoding="utf-8", errors="ignore")
            # Safe check: if it mentions cron but does not install it, that is okay
            mentions_cron = "cron" in content.lower()
            installs_cron = "crontab" in content.lower() and ("install" in content.lower() or "add" in content.lower())
            if mentions_cron and not installs_cron:
                audit.items.append({
                    "check": "scheduler_no_cron_install",
                    "file": tool_name,
                    "status": "pass",
                    "message": "Scheduler tool prints commands only, does not install cron",
                })
                audit.pass_count += 1
            elif installs_cron:
                audit.items.append({
                    "check": "scheduler_no_cron_install",
                    "file": tool_name,
                    "status": "fail",
                    "message": "Scheduler tool may install cron automatically",
                })
                audit.fail_count += 1
            else:
                audit.items.append({
                    "check": "scheduler_no_cron_install",
                    "file": tool_name,
                    "status": "pass",
                    "message": "No cron references found",
                })
                audit.pass_count += 1

    # Check no auto-send email/Telegram
    auto_send_tools = ["generate_email_briefing_text.py", "generate_telegram_briefing_text.py"]
    for tool_name in auto_send_tools:
        tool_path = tools_dir / tool_name if tools_dir.exists() else None
        if tool_path and tool_path.exists():
            content = tool_path.read_text(encoding="utf-8", errors="ignore")
            # Phase 23: check for actual send calls, not just text generation
            has_actual_send = False
            lines = content.splitlines()
            for line in lines:
                stripped = line.strip().lower()
                # Skip comments
                if stripped.startswith("#"):
                    continue
                # Look for actual send/POST/smtp.sendmail patterns
                if any(pattern in stripped for pattern in [".send(", "sendmail(", "post(", "requests.post"]):
                    has_actual_send = True
                    break
            if has_actual_send:
                audit.items.append({
                    "check": "no_auto_send",
                    "file": tool_name,
                    "status": "warning",
                    "message": "Tool may contain actual send logic; verify it is text-only generation",
                })
                audit.warning_count += 1
            else:
                audit.items.append({
                    "check": "no_auto_send",
                    "file": tool_name,
                    "status": "pass",
                    "message": "Tool generates text only, no send logic detected",
                })
                audit.pass_count += 1

    return audit
