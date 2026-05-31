"""Tests for Phase 24 operator status and flow.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from local_app.operator_status import build_operator_status, render_operator_summary, OperatorStatus


def _make_config():
    return {
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "directories": {
            "reports": "reports",
            "briefing": "reports/briefing",
            "dashboard": "reports/dashboard",
        },
        "dashboard": {"host": "127.0.0.1", "port": 8000},
    }


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestOperatorStatusBuild:
    def test_build_from_temp_root_with_allow_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            status = build_operator_status(config, root, allow_missing=True)
            assert status.paper_only is True
            assert status.data_only is True
            assert status.no_order_submission is True
            assert status.overall in ("OK", "OK_WITH_WARNINGS")

    def test_missing_optional_artifacts_do_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            status = build_operator_status(config, root, allow_missing=True)
            assert status.readiness_score is None
            assert status.latest_briefing_path is None
            assert status.latest_dashboard_path is None
            assert any("readiness" in w.lower() for w in status.warnings)
            assert any("briefing" in w.lower() for w in status.warnings)

    def test_missing_optional_produce_warning_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            status = build_operator_status(config, root, allow_missing=True)
            assert status.overall == "OK_WITH_WARNINGS"
            assert len(status.warnings) > 0
            assert len(status.blockers) == 0

    def test_workflow_summary_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            workflow = {
                "timestamp": "2026-05-31T00:00:00+00:00",
                "steps": [
                    {"step": "init", "status": "success"},
                    {"step": "run", "status": "success"},
                ],
                "overall_status": "success",
            }
            _write_json(root / "reports" / "local_app" / "workflow_summary.json", workflow)
            status = build_operator_status(config, root, allow_missing=True)
            assert status.workflow_steps_completed == 2
            assert status.workflow_steps_total == 2
            assert status.workflow_timestamp == "2026-05-31T00:00:00+00:00"

    def test_workflow_failed_step_adds_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            workflow = {
                "timestamp": "2026-05-31T00:00:00+00:00",
                "steps": [
                    {"step": "init", "status": "success"},
                    {"step": "run", "status": "failed"},
                ],
                "overall_status": "failed",
            }
            _write_json(root / "reports" / "local_app" / "workflow_summary.json", workflow)
            status = build_operator_status(config, root, allow_missing=True)
            assert any("failed" in b.lower() for b in status.blockers)
            assert status.overall == "BLOCKED"

    def test_readiness_report_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            readiness = {
                "score": {"score": 70, "grade": "C", "status": "PAPER_MVP_READY_WITH_WARNINGS"},
            }
            _write_json(root / "reports" / "readiness_gate" / "readiness_report.json", readiness)
            status = build_operator_status(config, root, allow_missing=True)
            assert status.readiness_score == 70
            assert status.readiness_grade == "C"
            assert status.readiness_status == "PAPER_MVP_READY_WITH_WARNINGS"

    def test_briefing_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            briefing_dir = root / "reports" / "briefing"
            briefing_dir.mkdir(parents=True, exist_ok=True)
            (briefing_dir / "briefing_20260531.md").write_text("test briefing", encoding="utf-8")
            status = build_operator_status(config, root, allow_missing=True)
            assert status.briefing_status == "available"
            assert status.latest_briefing_path is not None

    def test_dashboard_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            dash_dir = root / "reports" / "dashboard"
            dash_dir.mkdir(parents=True, exist_ok=True)
            (dash_dir / "dashboard_20260531.json").write_text("{}", encoding="utf-8")
            status = build_operator_status(config, root, allow_missing=True)
            assert status.dashboard_status == "available"
            assert status.latest_dashboard_path is not None

    def test_next_safe_commands_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            status = build_operator_status(config, root, allow_missing=True)
            assert any("run_local_dashboard" in c for c in status.next_safe_commands)
            assert any("8000" in c for c in status.next_safe_commands)

    def test_no_hardcoded_user_paths_in_source(self):
        source_path = PROJECT_ROOT / "local_app" / "operator_status.py"
        content = source_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found: {f}"

    def test_no_live_trading_keywords_in_source(self):
        source_path = PROJECT_ROOT / "local_app" / "operator_status.py"
        content = source_path.read_text(encoding="utf-8")
        assert "PAPER-ONLY" in content or "paper_only" in content
        assert "DATA-ONLY" in content or "data_only" in content


class TestRenderOperatorSummary:
    def test_contains_paper_only_data_only(self):
        status = OperatorStatus()
        text = render_operator_summary(status)
        assert "paper-only" in text.lower()
        assert "data-only" in text.lower()

    def test_contains_no_live_trading(self):
        status = OperatorStatus()
        text = render_operator_summary(status)
        assert "live trading" in text.lower()

    def test_contains_no_order_submission(self):
        status = OperatorStatus()
        text = render_operator_summary(status)
        assert "order" in text.lower()
        assert "submission" in text.lower() or "submit" in text.lower()

    def test_contains_next_safe_commands(self):
        status = OperatorStatus()
        status.next_safe_commands = ["python3 tools/run_local_dashboard.py"]
        text = render_operator_summary(status)
        assert "Next safe commands" in text
        assert "run_local_dashboard" in text

    def test_contains_reminder_not_to_commit(self):
        status = OperatorStatus()
        text = render_operator_summary(status)
        assert "not be committed" in text.lower()

    def test_overall_blocked_shown(self):
        status = OperatorStatus()
        status.blockers = ["Test blocker"]
        status.overall = "BLOCKED"
        text = render_operator_summary(status)
        assert "BLOCKED" in text
        assert "Test blocker" in text

    def test_warnings_count_shown(self):
        status = OperatorStatus()
        status.warnings = ["Warning 1", "Warning 2"]
        text = render_operator_summary(status)
        assert "Warnings (2)" in text
        assert "Warning 1" in text
        assert "Warning 2" in text
