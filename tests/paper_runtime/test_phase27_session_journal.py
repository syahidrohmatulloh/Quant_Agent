"""Tests for Phase 27 paper runtime session journal module.

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

from paper_runtime.session_journal import (
    PaperRuntimeSession,
    PaperRuntimeJournal,
    build_paper_runtime_session,
    build_paper_runtime_journal,
    write_paper_runtime_journal,
    render_paper_runtime_summary,
    load_latest_paper_runtime_session,
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


class TestBuildPaperRuntimeSession:
    def test_build_with_no_outputs_and_allow_missing_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert session.paper_only is True
            assert session.data_only is True
            assert session.no_order_submission is True
            assert session.workflow_status == "not_found"
            assert len(session.warnings) > 0
            assert any("No paper runtime outputs found yet" in w for w in session.warnings)

    def test_missing_outputs_return_warnings_not_crashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert isinstance(session, PaperRuntimeSession)
            assert len(session.warnings) > 0
            assert len(session.blockers) == 0

    def test_malformed_json_returns_warning_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            bad_dir = root / "reports" / "local_app"
            bad_dir.mkdir(parents=True, exist_ok=True)
            (bad_dir / "workflow_summary.json").write_text("not json", encoding="utf-8")
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert isinstance(session, PaperRuntimeSession)
            assert session.workflow_status == "not_found"

    def test_build_session_reads_workflow_summary_json_if_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            wf_dir = root / "reports" / "local_app"
            wf_dir.mkdir(parents=True, exist_ok=True)
            _write_json(wf_dir / "workflow_summary.json", {
                "timestamp": "2026-05-31T10:00:00Z",
                "steps": [
                    {"step": "init", "status": "success"},
                    {"step": "run", "status": "success"},
                ],
                "signals": [{"symbol": "EURUSD", "direction": "long"}],
            })
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert session.workflow_status == "completed"
            assert len(session.workflow_steps) == 2
            assert session.signal_summary["status"] == "available"
            assert session.signal_summary["count"] == 1

    def test_build_session_extracts_workflow_status_and_steps_if_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            wf_dir = root / "reports" / "local_app"
            wf_dir.mkdir(parents=True, exist_ok=True)
            _write_json(wf_dir / "workflow_summary.json", {
                "steps": [
                    {"step": "a", "status": "success"},
                    {"step": "b", "status": "warning"},
                    {"step": "c", "status": "failed"},
                ],
            })
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert session.workflow_status.startswith("failed")
            assert len(session.workflow_steps) == 3
            assert len(session.risk_warnings) > 0

    def test_build_session_detects_generated_outputs_if_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            dash_dir = root / "reports" / "dashboard"
            dash_dir.mkdir(parents=True, exist_ok=True)
            _write_json(dash_dir / "dash.json", {"test": True})
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            assert len(session.generated_outputs) > 0
            assert any("dash.json" in p for p in session.generated_outputs)


class TestWritePaperRuntimeJournal:
    def test_write_journal_writes_jsonl_latest_json_markdown_to_temp_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            session = build_paper_runtime_session(root, config=config, allow_missing=True)
            written = write_paper_runtime_journal(root, session, config=config)
            assert "journal" in written
            assert "latest_session" in written
            assert "summary" in written
            journal_path = root / "reports" / "paper_runtime" / "session_journal.jsonl"
            assert journal_path.exists()
            latest_path = root / "reports" / "paper_runtime" / "latest_session.json"
            assert latest_path.exists()
            summary_path = root / "reports" / "paper_runtime" / "session_summary.md"
            assert summary_path.exists()


class TestRenderSummary:
    def test_render_summary_includes_paper_only_data_only(self):
        session = PaperRuntimeSession()
        text = render_paper_runtime_summary(session)
        assert "PAPER-ONLY" in text
        assert "DATA-ONLY" in text

    def test_render_summary_includes_no_live_trading(self):
        session = PaperRuntimeSession()
        text = render_paper_runtime_summary(session)
        assert "No live trading" in text

    def test_render_summary_includes_not_financial_advice(self):
        session = PaperRuntimeSession()
        text = render_paper_runtime_summary(session)
        assert "not financial advice" in text.lower()

    def test_render_summary_includes_next_safe_commands(self):
        session = PaperRuntimeSession()
        session.next_safe_commands = ["python3 tools/test.py"]
        text = render_paper_runtime_summary(session)
        assert "Next Safe Commands" in text
        assert "python3 tools/test.py" in text

    def test_render_journal_summary(self):
        journal = PaperRuntimeJournal()
        journal.latest_session = PaperRuntimeSession()
        text = render_paper_runtime_summary(journal)
        assert "PAPER-ONLY" in text


class TestLoadLatestSession:
    def test_load_latest_returns_none_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            result = load_latest_paper_runtime_session(root, config=config)
            assert result is None

    def test_load_latest_returns_session_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            session = PaperRuntimeSession(session_id="test123", workflow_status="completed")
            write_paper_runtime_journal(root, session, config=config)
            loaded = load_latest_paper_runtime_session(root, config=config)
            assert loaded is not None
            assert loaded.session_id == "test123"
            assert loaded.workflow_status == "completed"


class TestNoHardcodedPaths:
    def test_no_hardcoded_user_paths_in_source(self):
        source_path = PROJECT_ROOT / "paper_runtime" / "session_journal.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found: {f}"

    def test_no_forbidden_raw_literals_in_source(self):
        source_path = PROJECT_ROOT / "paper_runtime" / "session_journal.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"
