"""Tests for message_templates.

Covers:
- email-ready text generated but not sent
- telegram-ready text generated but not sent
- telegram text respects max length
"""

import tempfile
from pathlib import Path

from briefing.message_templates import generate_email_text, generate_telegram_text, write_email_text, write_telegram_text


def make_briefing():
    return {
        "name": "test",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "summary": {
            "headline": "All ok",
            "market_data_status": "ok",
            "experiment_status": "ok",
            "paper_portfolio_status": "0 positions",
            "simulated_pnl_status": "PnL: 0.0",
            "risk_status": "Exposure: 0%",
            "alert_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
        },
        "alerts": [],
        "sections": {
            "signals": {},
            "portfolio": {},
            "simulated_pnl": {"total_pnl": 0.0, "drawdown_pct": 0.0, "total_costs": 0.0},
            "risk": {},
            "data_quality": {},
            "research_analytics": {},
            "next_steps": ["Review"],
        },
        "warnings": [],
        "errors": [],
    }


def make_config():
    return {
        "message": {
            "timezone": "Asia/Jakarta",
            "tone": "professional",
            "include_disclaimer": True,
            "include_next_steps": True,
            "max_telegram_chars": 3500,
        }
    }


def test_email_text_contains_disclaimer():
    text = generate_email_text(make_briefing(), make_config())
    assert "paper trading only" in text.lower()
    assert "Subject:" in text
    assert "Greetings" in text
    assert "not financial advice" in text.lower()
    assert "Do not place real trades" in text


def test_telegram_text_compact():
    text = generate_telegram_text(make_briefing(), make_config())
    assert len(text) <= 3500
    assert "Paper-only" in text or "paper-only" in text.lower()
    assert "not financial advice" in text.lower()


def test_telegram_text_truncates():
    briefing = make_briefing()
    briefing["alerts"] = [
        {
            "severity": "INFO",
            "category": "system",
            "title": f"Alert {i}",
            "message": "x" * 500,
            "source": "test",
            "generated_at": "2024-01-01T00:00:00+00:00",
            "timezone": "UTC",
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }
        for i in range(50)
    ]
    text = generate_telegram_text(briefing, make_config())
    assert len(text) <= 3500
    assert "truncated" in text or len(text) < 3500


def test_write_email_text_creates_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "email.txt"
        write_email_text(make_briefing(), make_config(), p)
        assert p.exists()
        assert "paper trading only" in p.read_text().lower()


def test_write_telegram_text_creates_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "tg.txt"
        write_telegram_text(make_briefing(), make_config(), p)
        assert p.exists()
        assert "Paper-only" in p.read_text() or "paper-only" in p.read_text().lower()
