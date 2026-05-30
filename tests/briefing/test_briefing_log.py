"""Tests for briefing_log.

Covers:
- append-only JSONL
- record shape
"""

import json
import tempfile
from pathlib import Path

from briefing.briefing_log import append_briefing_log


def make_briefing():
    return {
        "name": "test",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "summary": {
            "headline": "ok",
            "alert_count": 2,
            "critical_count": 1,
            "warning_count": 1,
            "info_count": 0,
        },
        "sections": {
            "signals": {},
            "portfolio": {},
            "simulated_pnl": {},
            "risk": {},
            "data_quality": {},
            "research_analytics": {},
        },
        "alerts": [],
        "warnings": [],
        "errors": [],
    }


def test_append_creates_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "log.jsonl"
        append_briefing_log(make_briefing(), p)
        assert p.exists()
        lines = p.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["briefing_id"].startswith("test_")
        assert record["paper_only"] is True
        assert record["data_only"] is True
        assert record["no_order_submission"] is True
        assert record["alert_count"] == 0  # alerts list is empty in test fixture


def test_append_is_append_only():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "log.jsonl"
        append_briefing_log(make_briefing(), p)
        append_briefing_log(make_briefing(), p)
        lines = p.read_text().strip().split("\n")
        assert len(lines) == 2
