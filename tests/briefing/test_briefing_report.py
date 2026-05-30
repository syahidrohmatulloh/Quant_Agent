"""Tests for briefing_report.

Covers:
- markdown report writes file
- JSON report writes file
- alert summary JSON writes file
"""

import json
import tempfile
from pathlib import Path

from briefing.briefing_report import write_markdown_report, write_json_report, write_alert_summary


def make_briefing():
    return {
        "name": "test",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "summary": {
            "headline": "Test headline",
            "market_data_status": "ok",
            "experiment_status": "ok",
            "paper_portfolio_status": "0 positions",
            "simulated_pnl_status": "PnL: 0.0",
            "risk_status": "Exposure: 0%",
            "alert_count": 1,
            "critical_count": 0,
            "warning_count": 1,
            "info_count": 0,
        },
        "alerts": [
            {
                "severity": "WARNING",
                "category": "data_quality",
                "title": "Low Quality",
                "message": "Quality low",
                "source": "test",
                "generated_at": "2024-01-01T00:00:00+00:00",
                "timezone": "UTC",
                "paper_only": True,
                "data_only": True,
                "no_order_submission": True,
            }
        ],
        "sections": {
            "signals": {},
            "portfolio": {},
            "simulated_pnl": {"total_pnl": 0.0, "drawdown_pct": 0.0, "total_costs": 0.0},
            "risk": {},
            "data_quality": {"catalog_status": "ok", "quality_score": 0.9, "dataset_count": 1},
            "research_analytics": {},
            "next_steps": ["Review"],
        },
        "warnings": [],
        "errors": [],
    }


def test_write_markdown_report():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "brief.md"
        write_markdown_report(make_briefing(), p)
        assert p.exists()
        text = p.read_text()
        assert "Daily Briefing" in text
        assert "paper trading only" in text.lower()
        assert "DISCLAIMER" in text


def test_write_json_report():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "brief.json"
        write_json_report(make_briefing(), p)
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["name"] == "test"


def test_write_alert_summary():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "alerts.json"
        write_alert_summary(make_briefing(), p)
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["alert_count"] == 1
        assert data["paper_only"] is True
