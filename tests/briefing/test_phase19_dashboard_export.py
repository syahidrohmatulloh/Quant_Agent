"""Tests for dashboard_export.

Covers:
- dashboard export writes expected shape
"""

import json
import tempfile
from pathlib import Path

from briefing.dashboard_export import export_dashboard_json


def make_briefing():
    return {
        "name": "test",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "summary": {
            "headline": "ok",
            "market_data_status": "ok",
            "experiment_status": "ok",
            "paper_portfolio_status": "0",
            "simulated_pnl_status": "0",
            "risk_status": "0%",
            "alert_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
        },
        "alerts": [],
        "sections": {
            "signals": {"consensus": "NEUTRAL"},
            "portfolio": {},
            "simulated_pnl": {},
            "risk": {},
            "data_quality": {},
            "research_analytics": {},
            "next_steps": [],
        },
        "warnings": [],
        "errors": [],
    }


def test_dashboard_export_shape():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dash.json"
        export_dashboard_json(make_briefing(), p)
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["name"] == "test"
        assert data["paper_only"] is True
        assert data["data_only"] is True
        assert data["no_order_submission"] is True
        assert "headline" in data
        assert "alert_count" in data
        assert "top_alerts" in data
        assert "summary" in data
        assert "source_status" in data
        assert "warnings" in data
        assert "errors" in data
