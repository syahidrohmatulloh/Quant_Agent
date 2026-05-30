"""Generate email-ready and Telegram-ready briefing text.

Does NOT send email. Does NOT call Telegram API.
Only writes local text files.
"""

import json
from pathlib import Path
from typing import Any, Dict


def generate_email_text(briefing: Dict[str, Any], config: Dict[str, Any]) -> str:
    msg_cfg = config.get("message", {})
    timezone = msg_cfg.get("timezone", "UTC")
    tone = msg_cfg.get("tone", "professional")
    include_disclaimer = msg_cfg.get("include_disclaimer", True)
    include_next_steps = msg_cfg.get("include_next_steps", True)

    lines = []
    lines.append(f"Subject: Daily Paper Briefing - {briefing['name']} - {briefing['generated_at'][:10]}")
    lines.append("")
    lines.append("Greetings,")
    lines.append("")
    lines.append(f"Here is your daily paper-trading briefing for {briefing['name']}.")
    lines.append("")
    lines.append(f"Headline: {briefing['summary']['headline']}")
    lines.append("")

    lines.append("Alerts:")
    if briefing["alerts"]:
        for alert in briefing["alerts"][:10]:
            lines.append(f"  [{alert['severity']}] {alert['title']}: {alert['message']}")
    else:
        lines.append("  No alerts.")
    lines.append("")

    lines.append(f"Paper Portfolio: {briefing['summary']['paper_portfolio_status']}")
    lines.append(f"Simulated PnL: {briefing['summary']['simulated_pnl_status']}")
    lines.append(f"Risk: {briefing['summary']['risk_status']}")
    lines.append("")

    if include_next_steps:
        lines.append("Next Steps:")
        for step in briefing["sections"].get("next_steps", []):
            lines.append(f"  - {step}")
        lines.append("")

    if include_disclaimer:
        lines.append("DISCLAIMER:")
        lines.append("This briefing is for research and paper trading only.")
        lines.append("It is not financial advice and does not guarantee performance.")
        lines.append("Do not place real trades based on this report.")
        lines.append("")

    lines.append("Paper-only / data-only. No live trading. No order submission.")
    lines.append("")
    lines.append("Best regards,")
    lines.append("Quant Agent Briefing System")

    return "\n".join(lines)


def generate_telegram_text(briefing: Dict[str, Any], config: Dict[str, Any]) -> str:
    msg_cfg = config.get("message", {})
    max_chars = msg_cfg.get("max_telegram_chars", 3500)
    timezone = msg_cfg.get("timezone", "UTC")

    lines = []
    lines.append(f"📊 Daily Paper Briefing: {briefing['name']}")
    lines.append(f"🕒 {briefing['generated_at'][:16]} {timezone}")
    lines.append("")

    # Emoji by severity
    headline = briefing["summary"]["headline"]
    critical = briefing["summary"]["critical_count"]
    if critical > 0:
        lines.append(f"🔴 {headline}")
    elif briefing["summary"]["warning_count"] > 0:
        lines.append(f"🟡 {headline}")
    else:
        lines.append(f"🟢 {headline}")
    lines.append("")

    if briefing["alerts"]:
        lines.append("Alerts:")
        for alert in briefing["alerts"][:8]:
            sev_emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(alert["severity"], "⚪")
            lines.append(f"{sev_emoji} {alert['title']}")
        lines.append("")

    lines.append(f"Portfolio: {briefing['summary']['paper_portfolio_status']}")
    lines.append(f"Sim PnL: {briefing['summary']['simulated_pnl_status']}")
    lines.append(f"Risk: {briefing['summary']['risk_status']}")
    lines.append("")

    lines.append("Next: review manually, keep paper-only, do not trade live.")
    lines.append("")
    lines.append("⚠️ Paper-only. Not financial advice. No real trades.")

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars - 50]
        text = text + "\n... (truncated)\n"
    return text


def write_email_text(briefing: Dict[str, Any], config: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = generate_email_text(briefing, config)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_telegram_text(briefing: Dict[str, Any], config: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = generate_telegram_text(briefing, config)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
