"""Tests for briefing_builder.

Covers:
- briefing builder creates expected summary shape
- alert counts correct
- sections present
"""

from briefing.briefing_builder import build_briefing


def make_config():
    return {
        "name": "test_briefing",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "sources": {},
        "outputs": {},
        "alert_rules": {
            "alert_on_signal_change": True,
            "alert_on_exposure_warning": True,
            "alert_on_data_quality_warning": True,
            "alert_on_negative_simulated_pnl": True,
            "alert_on_large_drawdown": True,
            "alert_on_missing_sources": True,
            "simulated_pnl_warning_threshold": -500.0,
            "drawdown_warning_threshold_pct": -5.0,
            "max_alerts_per_briefing": 20,
        },
        "message": {"timezone": "Asia/Jakarta"},
    }


def test_briefing_shape():
    loaded = {
        "sources": {
            "experiment_dashboard": {"signals": {"consensus": "LONG", "strategy_votes": {"s1": "LONG"}}, "status": "ok"},
            "paper_simulator_state": {
                "total_pnl": -600.0,
                "drawdown_pct": -0.06,
                "exposure": {"gross_exposure": 1.2, "short_exposure": 0.1, "symbol_concentration": {"EURUSD": 0.6}},
                "portfolio": {"positions": [{"symbol": "EURUSD", "direction": "LONG", "size": 1.0}]},
                "total_costs": 10.0,
            },
            "data_manager_catalog": {"quality_score": 0.5, "datasets": [{"name": "fx", "status": "missing"}]},
            "data_manager_import_log": [{"status": "warning", "message": "slow", "row_count": 50, "dataset": "fx"}],
        },
        "warnings": [],
    }
    briefing = build_briefing(make_config(), loaded)
    assert briefing["name"] == "test_briefing"
    assert briefing["paper_only"] is True
    assert briefing["data_only"] is True
    assert briefing["no_order_submission"] is True
    assert "summary" in briefing
    assert "alerts" in briefing
    assert "sections" in briefing
    assert briefing["summary"]["alert_count"] > 0
    assert briefing["summary"]["critical_count"] >= 0
    assert briefing["summary"]["warning_count"] >= 0
    assert briefing["summary"]["info_count"] >= 0
    assert "headline" in briefing["summary"]
    assert "signals" in briefing["sections"]
    assert "portfolio" in briefing["sections"]
    assert "simulated_pnl" in briefing["sections"]
    assert "risk" in briefing["sections"]
    assert "data_quality" in briefing["sections"]
    assert "research_analytics" in briefing["sections"]
    assert "next_steps" in briefing["sections"]


def test_briefing_with_missing_sources():
    loaded = {
        "sources": {"experiment_dashboard": None},
        "warnings": ["Missing source: experiment_dashboard"],
    }
    briefing = build_briefing(make_config(), loaded)
    assert any(a["category"] == "missing_source" for a in briefing["alerts"])


def test_briefing_no_alerts_when_all_ok():
    loaded = {
        "sources": {
            "experiment_dashboard": {"signals": {"consensus": "NEUTRAL", "strategy_votes": {"s1": "NEUTRAL"}}, "status": "ok"},
            "paper_simulator_state": {
                "total_pnl": 100.0,
                "drawdown_pct": -0.01,
                "exposure": {"gross_exposure": 0.5, "short_exposure": 0.0, "symbol_concentration": {}},
                "portfolio": {"positions": []},
                "total_costs": 1.0,
            },
            "data_manager_catalog": {"quality_score": 0.9, "datasets": [{"name": "fx", "status": "ok"}]},
            "data_manager_import_log": [{"status": "ok", "message": "done", "row_count": 1000, "dataset": "fx"}],
        },
        "warnings": [],
    }
    briefing = build_briefing(make_config(), loaded)
    assert briefing["summary"]["alert_count"] == 0 or all(a["severity"] == "INFO" for a in briefing["alerts"])
