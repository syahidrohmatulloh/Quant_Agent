"""Tests for Phase 25 action center.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from local_app.action_center import (
    ActionCenter,
    build_operator_action_center,
    render_action_center_summary,
    categorize_readiness_findings,
)

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

class TestCategorizeReadinessFindings:
    def test_empty_data_returns_unknown(self):
        result = categorize_readiness_findings(None)
        assert "unknown" in result
        assert len(result["unknown"]) == 1

    def test_config_findings_categorized(self):
        data = {
            "findings": [
                {"message": "Missing config file", "severity": "error"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["config"]) == 1
        assert "Missing config file" in result["config"][0]

    def test_data_findings_categorized(self):
        data = {
            "findings": [
                {"message": "CSV dataset missing", "severity": "warning"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["data"]) == 1

    def test_safety_findings_categorized(self):
        data = {
            "findings": [
                {"message": "Live trading flag detected", "severity": "critical"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["safety"]) == 1

    def test_test_findings_categorized(self):
        data = {
            "findings": [
                {"message": "pytest coverage below threshold", "severity": "warning"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["tests"]) == 1

    def test_doc_findings_categorized(self):
        data = {
            "findings": [
                {"message": "README markdown incomplete", "severity": "warning"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["docs"]) == 1

    def test_no_findings_but_score_returns_empty(self):
        data = {"score": {"score": 85, "grade": "B"}}
        result = categorize_readiness_findings(data)
        assert all(len(v) == 0 for v in result.values())

    def test_unknown_findings_fallback(self):
        data = {
            "findings": [
                {"message": "Something weird happened", "severity": "warning"},
            ]
        }
        result = categorize_readiness_findings(data)
        assert len(result["unknown"]) == 1

class TestBuildOperatorActionCenter:
    def test_build_from_temp_root_with_allow_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert ac.paper_only is True
            assert ac.data_only is True
            assert ac.no_order_submission is True
            assert ac.overall in ("OK", "OK_WITH_WARNINGS")

    def test_missing_optional_artifacts_produce_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert ac.readiness_score is None
            assert ac.latest_operator_run is None
            assert any("readiness" in w.lower() for w in ac.warnings)
            assert any("briefing" in w.lower() for w in ac.warnings)

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
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert any("failed" in b.lower() for b in ac.blockers)
            assert any("Fix workflow step" in item for item in ac.workflow_action_items)
            assert ac.overall == "BLOCKED"

    def test_workflow_warning_step_adds_action_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            workflow = {
                "timestamp": "2026-05-31T00:00:00+00:00",
                "steps": [
                    {"step": "init", "status": "success"},
                    {"step": "run", "status": "warning"},
                ],
                "overall_status": "warning",
            }
            _write_json(root / "reports" / "local_app" / "workflow_summary.json", workflow)
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert any("warning" in w.lower() for w in ac.warnings)
            assert any("Review workflow step" in item for item in ac.workflow_action_items)

    def test_readiness_below_70_adds_action_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            readiness = {
                "score": {"score": 65, "grade": "D", "status": "NEEDS_IMPROVEMENT"},
                "findings": [
                    {"message": "Low coverage", "severity": "warning"},
                ],
            }
            _write_json(root / "reports" / "readiness_gate" / "readiness_report.json", readiness)
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert ac.readiness_score == 65
            assert any("below 70" in item for item in ac.readiness_action_items)

    def test_readiness_above_70_no_action_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            readiness = {
                "score": {"score": 85, "grade": "B", "status": "PAPER_MVP_READY"},
            }
            _write_json(root / "reports" / "readiness_gate" / "readiness_report.json", readiness)
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert ac.readiness_score == 85
            assert len(ac.readiness_action_items) == 0

    def test_briefing_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            briefing_dir = root / "reports" / "briefing"
            briefing_dir.mkdir(parents=True, exist_ok=True)
            (briefing_dir / "briefing_20260531.md").write_text("test briefing", encoding="utf-8")
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert any("briefing_20260531.md" in p for p in ac.generated_outputs)
            assert len(ac.briefing_action_items) == 0

    def test_dashboard_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            dash_dir = root / "reports" / "dashboard"
            dash_dir.mkdir(parents=True, exist_ok=True)
            (dash_dir / "dashboard_20260531.json").write_text("{}", encoding="utf-8")
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert any("dashboard_20260531.json" in p for p in ac.generated_outputs)
            assert len(ac.dashboard_action_items) == 0

    def test_next_safe_commands_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert any("run_operator_day" in c for c in ac.next_safe_commands)
            assert any("show_local_app_status" in c for c in ac.next_safe_commands)
            assert any("run_local_dashboard" in c for c in ac.next_safe_commands)
            assert any("8000" in c for c in ac.next_safe_commands)

    def test_operator_status_timestamp_carried_forward(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            op_status = {
                "timestamp": "2026-05-31T12:00:00+00:00",
                "warnings": ["Old warning"],
                "blockers": [],
            }
            _write_json(root / "reports" / "local_app" / "operator_status.json", op_status)
            ac = build_operator_action_center(config, root, allow_missing=True)
            assert ac.latest_operator_run == "2026-05-31T12:00:00+00:00"
            assert "Old warning" in ac.warnings

    def test_no_hardcoded_user_paths_in_source(self):
        source_path = PROJECT_ROOT / "local_app" / "action_center.py"
        content = source_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found: {f}"

    def test_no_live_trading_keywords_in_source(self):
        source_path = PROJECT_ROOT / "local_app" / "action_center.py"
        content = source_path.read_text(encoding="utf-8")
        assert "PAPER-ONLY" in content or "paper_only" in content
        assert "DATA-ONLY" in content or "data_only" in content

class TestRenderActionCenterSummary:
    def test_contains_paper_only_data_only(self):
        ac = ActionCenter()
        text = render_action_center_summary(ac)
        assert "paper-only" in text.lower()
        assert "data-only" in text.lower()

    def test_contains_no_live_trading(self):
        ac = ActionCenter()
        text = render_action_center_summary(ac)
        assert "live trading" in text.lower()

    def test_contains_action_items(self):
        ac = ActionCenter()
        ac.readiness_action_items = ["Fix coverage"]
        ac.workflow_action_items = ["Review step"]
        text = render_action_center_summary(ac)
        assert "Fix coverage" in text
        assert "Review step" in text

    def test_contains_warning_categories(self):
        ac = ActionCenter()
        ac.warning_categories = {"config": ["[ERROR] Missing file"]}
        text = render_action_center_summary(ac)
        assert "CONFIG" in text
        assert "Missing file" in text

    def test_contains_next_safe_commands(self):
        ac = ActionCenter()
        ac.next_safe_commands = ["python3 tools/run_operator_day.py"]
        text = render_action_center_summary(ac)
        assert "Next safe commands" in text
        assert "run_operator_day" in text

    def test_overall_blocked_shown(self):
        ac = ActionCenter()
        ac.blockers = ["Test blocker"]
        ac.overall = "BLOCKED"
        text = render_action_center_summary(ac)
        assert "BLOCKED" in text
        assert "Test blocker" in text

    def test_contains_generated_outputs(self):
        ac = ActionCenter()
        ac.generated_outputs = ["reports/briefing/test.md"]
        text = render_action_center_summary(ac)
        assert "reports/briefing/test.md" in text
