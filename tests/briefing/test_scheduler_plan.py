"""Tests for scheduler_plan.

Covers:
- scheduler command generated but not installed
- command contains project root and config path
"""

from pathlib import Path

from briefing.scheduler_plan import generate_scheduler_command, generate_scheduler_plan


def make_config():
    return {"name": "test"}


def test_scheduler_command_contains_config():
    cmd = generate_scheduler_command(make_config(), Path("/project"), venv_python="python3")
    assert "generate_daily_briefing.py" in cmd
    assert "--config" in cmd
    assert "--allow-missing" in cmd


def test_scheduler_plan_is_text_only():
    plan = generate_scheduler_plan(make_config(), Path("/project"), venv_python="python3")
    assert "crontab" in plan.lower() or "cron" in plan.lower()
    assert "not installed" in plan.lower() or "manually" in plan.lower()
    assert "paper-only" in plan.lower()
    assert "no live trading" in plan.lower() or "paper-only" in plan.lower()
