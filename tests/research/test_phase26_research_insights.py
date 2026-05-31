"""Tests for Phase 26 research insights module.

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

from research_insights.insight_builder import (
    ResearchInsightSummary,
    StrategyInsight,
    build_research_insights,
    classify_strategy_metrics,
    render_research_insights_summary,
    load_strategy_outputs,
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


class TestBuildResearchInsights:
    def test_build_with_no_outputs_and_allow_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            summary = build_research_insights(root, config=config, allow_missing=True)
            assert summary.paper_only is True
            assert summary.data_only is True
            assert summary.no_order_submission is True
            assert summary.strategies == []
            assert "No strategy outputs found" in summary.warnings[0]

    def test_missing_outputs_return_warnings_not_crashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            summary = build_research_insights(root, config=config, allow_missing=True)
            assert len(summary.warnings) > 0
            assert len(summary.blockers) == 0

    def test_malformed_json_returns_warning_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            bad_dir = root / "reports" / "experiments"
            bad_dir.mkdir(parents=True, exist_ok=True)
            (bad_dir / "bad.json").write_text("not json", encoding="utf-8")
            summary = build_research_insights(root, config=config, allow_missing=True)
            # Should not crash; strategies may be empty since bad.json is skipped
            assert isinstance(summary, ResearchInsightSummary)


class TestClassifyStrategyMetrics:
    def test_good_metrics_returns_candidate(self):
        metrics = {"sharpe": 1.5, "win_rate": 0.60, "sample_size": 100, "return": 0.10}
        result = classify_strategy_metrics(metrics)
        assert result == "candidate_for_further_paper_testing"

    def test_bad_drawdown_returns_weak(self):
        metrics = {"drawdown": 0.30, "sample_size": 100, "return": 0.05}
        result = classify_strategy_metrics(metrics)
        assert result == "weak_paper_metrics"

    def test_low_sample_returns_needs_more_data(self):
        metrics = {"sharpe": 1.5, "win_rate": 0.60, "sample_size": 10}
        result = classify_strategy_metrics(metrics)
        assert result == "needs_more_data"

    def test_moderate_returns_monitor(self):
        metrics = {"sharpe": 0.7, "win_rate": 0.52, "sample_size": 100}
        result = classify_strategy_metrics(metrics)
        assert result == "monitor_in_paper_mode"

    def test_negative_return_returns_weak(self):
        metrics = {"return": -0.05, "sample_size": 100}
        result = classify_strategy_metrics(metrics)
        assert result == "weak_paper_metrics"

    def test_empty_returns_inconclusive(self):
        metrics = {}
        result = classify_strategy_metrics(metrics)
        assert result == "inconclusive"


class TestRenderSummary:
    def test_contains_paper_only_data_only(self):
        summary = ResearchInsightSummary()
        text = render_research_insights_summary(summary)
        assert "PAPER-ONLY" in text
        assert "DATA-ONLY" in text

    def test_contains_no_live_trading(self):
        summary = ResearchInsightSummary()
        text = render_research_insights_summary(summary)
        assert "No live trading" in text

    def test_contains_not_financial_advice(self):
        summary = ResearchInsightSummary()
        text = render_research_insights_summary(summary)
        assert "not financial advice" in text.lower()

    def test_contains_next_safe_commands(self):
        summary = ResearchInsightSummary()
        summary.next_safe_commands = ["python3 tools/run_research_analytics.py"]
        text = render_research_insights_summary(summary)
        assert "Next Safe Commands" in text
        assert "run_research_analytics" in text

    def test_contains_strategies_when_present(self):
        summary = ResearchInsightSummary()
        summary.strategies = [StrategyInsight(name="TestStrat", classification="candidate_for_further_paper_testing")]
        text = render_research_insights_summary(summary)
        assert "TestStrat" in text
        assert "candidate_for_further_paper_testing" in text

    def test_contains_top_candidates(self):
        summary = ResearchInsightSummary()
        summary.top_candidates = ["StratA"]
        text = render_research_insights_summary(summary)
        assert "StratA" in text
        assert "Top Candidates" in text

    def test_contains_weak_candidates(self):
        summary = ResearchInsightSummary()
        summary.weak_candidates = ["StratB"]
        text = render_research_insights_summary(summary)
        assert "StratB" in text
        assert "Weak Candidates" in text


class TestLoadStrategyOutputs:
    def test_loads_from_experiments_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            exp_dir = root / "reports" / "experiments"
            exp_dir.mkdir(parents=True, exist_ok=True)
            _write_json(exp_dir / "run_1.json", {
                "strategies": [
                    {"name": "MA_Cross", "metrics": {"sharpe": 1.2, "win_rate": 0.55, "sample_size": 50}}
                ]
            })
            outputs = load_strategy_outputs(root, config)
            assert len(outputs) == 1
            assert outputs[0].get("name") == "MA_Cross"

    def test_loads_from_research_analytics_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            ra_dir = root / "reports" / "research_analytics"
            ra_dir.mkdir(parents=True, exist_ok=True)
            _write_json(ra_dir / "analytics.json", {
                "strategies": [
                    {"name": "RSI_MeanRev", "metrics": {"sharpe": 0.8, "win_rate": 0.52, "sample_size": 80}}
                ]
            })
            outputs = load_strategy_outputs(root, config)
            assert len(outputs) == 1
            assert outputs[0].get("name") == "RSI_MeanRev"

    def test_returns_empty_when_no_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_config()
            outputs = load_strategy_outputs(root, config)
            assert outputs == []


class TestNoHardcodedPaths:
    def test_no_hardcoded_user_paths_in_source(self):
        source_path = PROJECT_ROOT / "research_insights" / "insight_builder.py"
        # If running from temp, source may not exist yet; skip if not found
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
        source_path = PROJECT_ROOT / "research_insights" / "insight_builder.py"
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
