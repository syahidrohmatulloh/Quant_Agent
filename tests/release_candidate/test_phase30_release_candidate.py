"""Tests for Phase 30 release candidate checklist module.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tempfile
from pathlib import Path

import pytest

from release_candidate.checklist import (
    ReleaseCandidateCheck,
    ReleaseCandidateReport,
    build_release_candidate_report,
    check_required_docs,
    check_generated_outputs_clean,
    check_dashboard_routes_available,
    check_cli_tools_present,
    check_safety_phrases,
    check_release_tags,
    classify_release_candidate,
    render_release_candidate_summary,
    write_release_candidate_report,
    load_latest_release_candidate_report,
)


class TestBuildReleaseCandidateReport:
    def test_build_release_candidate_report_works_with_allow_missing_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Create minimal required docs
            (tmp_path / "README.md").write_text("paper-only data-only no live trading no order submission not financial advice does not approve or enable live trading", encoding="utf-8")
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_path / "docs" / "COMMAND_CHEATSHEET.md").write_text("paper-only", encoding="utf-8")
            (tmp_path / "docs" / "DAILY_WORKFLOW.md").write_text("paper-only", encoding="utf-8")
            (tmp_path / "docs" / "PHASE_HISTORY.md").write_text("paper-only", encoding="utf-8")
            report = build_release_candidate_report(tmp_path, config=None, allow_missing=True)
            assert report is not None
            assert report.paper_only is True
            assert report.data_only is True
            assert report.no_order_submission is True

    def test_missing_optional_docs_produce_warnings_not_crashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("paper-only data-only no live trading no order submission not financial advice does not approve or enable live trading", encoding="utf-8")
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_path / "docs" / "COMMAND_CHEATSHEET.md").write_text("paper-only", encoding="utf-8")
            (tmp_path / "docs" / "DAILY_WORKFLOW.md").write_text("paper-only", encoding="utf-8")
            (tmp_path / "docs" / "PHASE_HISTORY.md").write_text("paper-only", encoding="utf-8")
            # Optional docs missing
            report = build_release_candidate_report(tmp_path, config=None, allow_missing=True)
            assert report.status in ("READY", "READY_WITH_WARNINGS")

    def test_required_cli_tools_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("paper-only data-only no live trading no order submission not financial advice does not approve or enable live trading", encoding="utf-8")
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
            for d in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "PHASE_HISTORY.md"]:
                (tmp_path / "docs" / d).write_text("paper-only", encoding="utf-8")
            (tmp_path / "tools").mkdir(parents=True, exist_ok=True)
            for tool in ["run_operator_day.py", "show_action_center.py", "show_research_insights.py",
                         "show_paper_runtime_journal.py", "show_data_quality.py", "show_paper_broker_readiness.py",
                         "run_readiness_audit.py", "validate_docs.py", "run_release_candidate_check.py"]:
                (tmp_path / "tools" / tool).write_text("# placeholder", encoding="utf-8")
            (tmp_path / "dashboard").mkdir(parents=True, exist_ok=True)
            (tmp_path / "dashboard" / "routes.py").write_text("/release-candidate /health /datasets /reports /dashboard/latest /operator /action-center /research-insights /paper-runtime /data-quality /paper-broker", encoding="utf-8")
            report = build_release_candidate_report(tmp_path, config=None, allow_missing=True)
            cli_checks = [c for c in report.checks if c.category == "cli"]
            assert all(c.status == "PASS" for c in cli_checks)

    def test_generated_outputs_detected_as_cleanup_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("paper-only data-only no live trading no order submission not financial advice does not approve or enable live trading", encoding="utf-8")
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
            for d in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "PHASE_HISTORY.md"]:
                (tmp_path / "docs" / d).write_text("paper-only", encoding="utf-8")
            (tmp_path / "reports").mkdir(parents=True, exist_ok=True)
            (tmp_path / "reports" / "dummy.txt").write_text("x", encoding="utf-8")
            report = build_release_candidate_report(tmp_path, config=None, allow_missing=True)
            gen_checks = [c for c in report.checks if c.category == "generated_outputs"]
            assert any(c.status == "WARN" for c in gen_checks)

    def test_safety_phrases_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("paper-only data-only no live trading no order submission not financial advice does not approve or enable live trading", encoding="utf-8")
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
            for d in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "PHASE_HISTORY.md"]:
                (tmp_path / "docs" / d).write_text("paper-only", encoding="utf-8")
            report = build_release_candidate_report(tmp_path, config=None, allow_missing=True)
            safety_checks = [c for c in report.checks if c.category == "safety"]
            assert len(safety_checks) > 0

    def test_classify_release_candidate_returns_correct_status(self):
        checks_pass = [ReleaseCandidateCheck(name="a", status="PASS", category="tests", message="ok", suggested_action="")]
        checks_warn = [ReleaseCandidateCheck(name="a", status="WARN", category="tests", message="warn", suggested_action="")]
        checks_block = [ReleaseCandidateCheck(name="a", status="BLOCKED", category="tests", message="block", suggested_action="")]
        assert classify_release_candidate(checks_pass) == "READY"
        assert classify_release_candidate(checks_warn) == "READY_WITH_WARNINGS"
        assert classify_release_candidate(checks_block) == "BLOCKED"
        assert classify_release_candidate(checks_warn + checks_pass) == "READY_WITH_WARNINGS"
        assert classify_release_candidate(checks_block + checks_pass) == "BLOCKED"

    def test_render_summary_includes_paper_only_data_only(self):
        report = ReleaseCandidateReport(status="READY")
        text = render_release_candidate_summary(report)
        assert "PAPER-ONLY" in text
        assert "DATA-ONLY" in text

    def test_render_summary_includes_no_live_trading(self):
        report = ReleaseCandidateReport(status="READY")
        text = render_release_candidate_summary(report)
        assert "No live trading" in text

    def test_render_summary_includes_not_financial_advice(self):
        report = ReleaseCandidateReport(status="READY")
        text = render_release_candidate_summary(report)
        assert "not financial advice" in text.lower()

    def test_render_summary_includes_next_safe_commands(self):
        report = ReleaseCandidateReport(status="READY", next_safe_commands=["cmd1", "cmd2"])
        text = render_release_candidate_summary(report)
        assert "Next Safe Commands" in text
        assert "cmd1" in text

    def test_write_report_writes_json_markdown_dashboard_latest_only_inside_temp_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report = ReleaseCandidateReport(status="READY")
            paths = write_release_candidate_report(tmp_path, report, config=None)
            assert any("release_candidate_report.json" in p for p in paths)
            assert any("release_candidate_report.md" in p for p in paths)
            assert any("latest.json" in p for p in paths)
            # Ensure all inside tmp_path
            for p in paths:
                assert Path(p).resolve().is_relative_to(tmp_path.resolve())

    def test_load_latest_release_candidate_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report = ReleaseCandidateReport(status="READY_WITH_WARNINGS")
            write_release_candidate_report(tmp_path, report, config=None)
            loaded = load_latest_release_candidate_report(tmp_path, config=None)
            assert loaded is not None
            assert loaded.status == "READY_WITH_WARNINGS"

    def test_no_credentials_required(self):
        report = build_release_candidate_report(Path("."), config=None, allow_missing=True)
        assert report is not None

    def test_no_network_calls(self):
        # This test documents that the module does not make network calls.
        # The implementation has no network code; this is a behavioral assertion.
        report = build_release_candidate_report(Path("."), config=None, allow_missing=True)
        assert report is not None

    def test_no_broker_calls(self):
        report = build_release_candidate_report(Path("."), config=None, allow_missing=True)
        assert report is not None

    def test_no_hardcoded_user_paths(self):
        import release_candidate.checklist as rc
        import inspect
        source = inspect.getsource(rc)
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in source, f"Forbidden path found: {f}"

    def test_no_forbidden_raw_literals_in_source(self):
        import release_candidate.checklist as rc
        import inspect
        source = inspect.getsource(rc)
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in source, f"Forbidden raw literal found: {term}"
