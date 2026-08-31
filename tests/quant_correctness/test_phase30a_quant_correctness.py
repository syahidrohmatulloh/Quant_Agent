"""Phase 30A quantitative correctness regression tests.

PAPER-ONLY / DATA-ONLY. No live trading. No external network calls.
"""
import csv
import math
from datetime import datetime
from pathlib import Path

import pytest

from backtesting.data_feed import HistoricalDataFeed
from backtesting.backtest_engine import BacktestEngine
from backtesting.event import FillEvent, PositionClosedEvent
from backtesting.performance import PerformanceAnalyzer
from backtesting.portfolio_simulator import PortfolioSimulator
from backtesting.walk_forward import WalkForward
from broker_integration.broker_config import BrokerConfig
from broker_integration.oanda.oanda_errors import OandaLiveEndpointError
from broker_integration.oanda.oanda_http_transport import OandaHttpTransport
from core.risk import RiskManager
from paper_broker.readiness import validate_paper_broker_config
from paper_simulator.exposure import compute_exposure
from paper_simulator.pnl_engine import compute_pnl
from paper_simulator.position_book import PositionBook
from paper_simulator.simulator_engine import SimulatorEngine
from research.example_strategies import DummyAlwaysBuy
from storage.audit import AuditLogger
from strategies.base import StrategyResult, StrategySignal
from strategy_lab.backtest import SimpleBacktestEngine


def _write_csv(path: Path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "open", "high", "low", "close", "volume"]
        )
        writer.writeheader()
        writer.writerows(rows)


def _sim_config(tmp_path: Path, csv_path: Path):
    return {
        "name": "phase30a_sim",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": str(tmp_path / "state.json"),
        "trade_log_path": str(tmp_path / "trades.jsonl"),
        "pnl_log_path": str(tmp_path / "pnl.jsonl"),
        "report_output": str(tmp_path / "report.md"),
        "dashboard_output": str(tmp_path / "dashboard.json"),
        "symbols": [{
            "symbol": "EURUSD",
            "timeframe": "H1",
            "csv": str(csv_path),
            "pip_size": 0.0001,
            "contract_size": 100000,
            "quote_currency": "USD",
        }],
        "execution": {
            "fill_price": "next_close",
            "allow_partial_fill": False,
            "max_fill_delay_bars": 1,
        },
        "costs": {
            "spread_pips": 0.0,
            "slippage_pips": 0.0,
            "commission_per_million": 0.0,
            "min_commission": 0.0,
        },
        "risk": {
            "max_symbol_weight": 1.0,
            "max_total_gross_exposure": 2.0,
            "allow_short": True,
            "max_notional_per_symbol": 1000000.0,
        },
    }


def test_exposure_one_standard_lot_is_notional_once(tmp_path):
    book = PositionBook(str(tmp_path / "state.json"))
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.10, 0.0)

    report = compute_exposure(
        book,
        {"EURUSD": 1.10},
        {"max_symbol_weight": 10.0, "max_total_gross_exposure": 10.0, "allow_short": True},
        100000.0,
    )

    assert report.gross_exposure == pytest.approx(110000.0)
    assert report.net_exposure == pytest.approx(110000.0)


def test_round_trip_costs_are_accounted_exactly_once(tmp_path):
    book = PositionBook(str(tmp_path / "state.json"))
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.10, 10.0)
    book.update_position("EURUSD", "H1", "SELL", 1.0, 1.10, 5.0)

    snapshot = compute_pnl(book, {"EURUSD": 1.10}, 100000.0, "USD")

    assert snapshot.realized_pnl == pytest.approx(0.0)
    assert snapshot.unrealized_pnl == pytest.approx(0.0)
    assert snapshot.total_costs == pytest.approx(15.0)
    assert snapshot.total_pnl == pytest.approx(-15.0)
    assert snapshot.equity == pytest.approx(99985.0)


def test_partial_close_reconciles_realized_unrealized_and_costs(tmp_path):
    book = PositionBook(str(tmp_path / "state.json"))
    book.update_position("EURUSD", "H1", "BUY", 2.0, 1.08, 10.0)
    book.update_position("EURUSD", "H1", "SELL", 1.0, 1.09, 5.0)

    snapshot = compute_pnl(book, {"EURUSD": 1.09}, 100000.0, "USD")

    assert snapshot.realized_pnl == pytest.approx(1000.0)
    assert snapshot.unrealized_pnl == pytest.approx(1000.0)
    assert snapshot.total_costs == pytest.approx(15.0)
    assert snapshot.total_pnl == pytest.approx(1985.0)


def test_reopening_flat_position_preserves_cumulative_ledger(tmp_path):
    book = PositionBook(str(tmp_path / "state.json"))
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.10, 2.0)
    closed = book.update_position("EURUSD", "H1", "SELL", 1.0, 1.11, 3.0)
    realized_before = closed.realized_pnl
    costs_before = closed.total_costs

    reopened = book.update_position("EURUSD", "H1", "BUY", 1.0, 1.12, 4.0)

    assert reopened.side == "LONG"
    assert reopened.realized_pnl == pytest.approx(realized_before)
    assert reopened.total_costs == pytest.approx(costs_before + 4.0)


def test_next_close_fill_uses_bar_after_decision_not_latest_bar(tmp_path):
    csv_path = tmp_path / "EURUSD_H1.csv"
    _write_csv(csv_path, [
        {"timestamp": "2024-01-01 00:00", "open": 1.00, "high": 1.01, "low": 0.99, "close": 1.00, "volume": 100},
        {"timestamp": "2024-01-01 01:00", "open": 1.10, "high": 1.21, "low": 1.09, "close": 1.20, "volume": 100},
        {"timestamp": "2024-01-01 02:00", "open": 9.80, "high": 10.0, "low": 9.70, "close": 9.90, "volume": 100},
    ])

    engine = SimulatorEngine(_sim_config(tmp_path, csv_path))
    engine.run([{
        "decision_id": "d1",
        "generated_at": "2024-01-01T00:00:00Z",
        "action": "PAPER_LONG",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "target_notional": 12000.0,
    }])

    assert len(engine.latest_fills) == 1
    assert engine.latest_fills[0].fill_price == pytest.approx(1.20)


def test_next_close_without_future_bar_fails_closed(tmp_path):
    csv_path = tmp_path / "EURUSD_H1.csv"
    _write_csv(csv_path, [
        {"timestamp": "2024-01-01 00:00", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 100},
    ])

    engine = SimulatorEngine(_sim_config(tmp_path, csv_path))
    engine.run([{
        "decision_id": "d1",
        "generated_at": "2024-01-02T00:00:00Z",
        "action": "PAPER_LONG",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "target_notional": 10000.0,
    }])

    assert engine.latest_fills == []
    assert any("causally valid price" in warning for warning in engine.warnings)


def test_portfolio_removes_closed_position_and_releases_margin():
    portfolio = PortfolioSimulator(100000.0)
    fill = FillEvent(datetime(2024, 1, 1), "EURUSD", "buy", 1.0, 1.10, 7.0)
    portfolio.on_fill(fill)
    assert portfolio.positions

    close = PositionClosedEvent(
        datetime(2024, 1, 1, 1),
        "EURUSD",
        "buy",
        1.0,
        1.10,
        1.10,
        -14.0,
        14.0,
    )
    portfolio.on_position_closed(close)

    assert portfolio.positions == {}
    assert portfolio.cash == pytest.approx(99986.0)
    assert portfolio.equity == pytest.approx(99986.0)


def test_backtest_engine_aggregates_repeated_same_direction_fills():
    data = [
        {"timestamp": f"2024-01-01T0{i}:00:00", "symbol": "EURUSD", "bid": 1.10, "ask": 1.1002}
        for i in range(3)
    ]
    engine = BacktestEngine(HistoricalDataFeed(data), DummyAlwaysBuy())
    result = engine.run()

    assert len(result["trades"]) == 1
    assert result["trades"][0]["volume"] == pytest.approx(3.0)
    assert engine.portfolio.positions == {}


class _AlwaysLong:
    def generate(self, data):
        sym = next(iter(data))
        ts = data[sym][-1]["timestamp"]
        return StrategyResult(signals=[StrategySignal(timestamp=ts, symbol=sym, signal="long")])


class _LongThenFlat:
    def generate(self, data):
        sym = next(iter(data))
        ts = data[sym][-1]["timestamp"]
        signal = "long" if len(data[sym]) == 1 else "flat"
        return StrategyResult(signals=[StrategySignal(timestamp=ts, symbol=sym, signal=signal)])


def _simple_bars():
    return {"TEST": [
        {"timestamp": datetime(2024, 1, 1, 0), "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1},
        {"timestamp": datetime(2024, 1, 1, 1), "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 1},
        {"timestamp": datetime(2024, 1, 1, 2), "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "volume": 1},
        {"timestamp": datetime(2024, 1, 1, 3), "open": 100.0, "high": 104.0, "low": 99.0, "close": 103.0, "volume": 1},
    ]}


def test_simple_backtest_does_not_double_count_unrealized_pnl():
    engine = SimpleBacktestEngine(
        _simple_bars(), _AlwaysLong(), initial_balance=1000.0, commission_rate=0.0
    )
    result = engine.run()

    assert result["equity_curve"] == pytest.approx([1000.0, 1001.0, 1002.0, 1003.0])


def test_simple_backtest_commission_is_charged_on_flat_round_trip():
    engine = SimpleBacktestEngine(
        _simple_bars(), _LongThenFlat(), initial_balance=1000.0, commission_rate=0.01
    )
    result = engine.run()

    assert len(result["trades"]) == 1
    assert result["trades"][0]["gross_pnl"] == pytest.approx(0.0)
    assert result["trades"][0]["commission"] == pytest.approx(2.0)
    assert result["trades"][0]["pnl"] == pytest.approx(-2.0)


@pytest.mark.parametrize("bad_volume", [0.0, -1.0, float("inf"), float("nan")])
def test_risk_manager_rejects_non_positive_or_non_finite_volume(bad_volume):
    decision = RiskManager(max_exposure=10.0).evaluate("EURUSD", "buy", bad_volume)
    assert decision.allowed is False


def test_risk_manager_applies_current_exposure():
    decision = RiskManager(max_exposure=5.0).evaluate(
        "EURUSD", "buy", 2.0, current_exposure=4.0
    )
    assert decision.allowed is False
    assert decision.checks["projected_exposure"] == pytest.approx(6.0)


def test_readiness_flags_and_mode_fail_closed_when_missing():
    config = {"broker_name": "paper_stub"}
    checks = validate_paper_broker_config(config)
    blocked = {c.name for c in checks if c.status == "BLOCKED"}

    assert "paper_only_flag" in blocked
    assert "data_only_flag" in blocked
    assert "no_order_submission_flag" in blocked
    assert "mode_check" in blocked


def test_readiness_unknown_mode_is_blocked():
    config = {
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "mode": "liv",
        "broker_name": "paper_stub",
    }
    checks = validate_paper_broker_config(config)
    assert any(c.name == "mode_check" and c.status == "BLOCKED" for c in checks)


def test_oanda_transport_rejects_practice_hostname_lookalike():
    config = BrokerConfig(
        broker_name="oanda",
        environment="practice",
        base_url="https://api-fxpractice.oanda.com.attacker.example",
    )
    with pytest.raises(OandaLiveEndpointError):
        OandaHttpTransport(config)


def test_performance_infers_hourly_annualization():
    timestamps = [
        "2024-01-01T00:00:00",
        "2024-01-01T01:00:00",
        "2024-01-01T02:00:00",
    ]
    perf = PerformanceAnalyzer([], [100000.0, 100100.0, 100050.0], timestamps)
    assert perf.periods_per_year == pytest.approx(252.0 * 24.0)


def test_audit_chain_resumes_across_logger_restart(tmp_path):
    path = str(tmp_path / "audit.jsonl")
    first_logger = AuditLogger(path)
    first = first_logger.log("event_a", "r1", "system", "admin", {"x": 1})

    second_logger = AuditLogger(path)
    second = second_logger.log("event_b", "r2", "system", "admin", {"x": 2})

    assert second["event_sequence"] == 2
    assert second["previous_event_hash"] == first["event_hash"]
    assert len(second["event_hash"]) == 64


def test_walk_forward_uses_training_hook_for_later_folds():
    seen_train_sizes = []

    def trainer(strategy, train_data):
        seen_train_sizes.append(len(train_data))
        return strategy

    data = [
        {"timestamp": f"2024-01-{i:02d}T00:00:00", "symbol": "EURUSD", "bid": 1.10, "ask": 1.1002}
        for i in range(1, 9)
    ]
    results = WalkForward(data, DummyAlwaysBuy, n_folds=4, trainer=trainer).run()

    assert [r["train_size"] for r in results] == [0, 2, 4, 6]
    assert seen_train_sizes == [2, 4, 6]
    assert results[0]["training_applied"] is False
    assert all(r["training_applied"] is True for r in results[1:])


def test_signal_generator_maps_binary_zero_class_to_sell():
    import numpy as np
    import pandas as pd
    from datetime import datetime, timezone
    from research_pipeline.model_registry import ModelRegistry, ModelEntry
    from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec
    from research_pipeline.model_trainer import SimpleRuleModel
    from signal_bridge.approved_model_loader import ApprovedModelLoader
    from signal_bridge.feature_runtime import FeatureRuntime
    from signal_bridge.prediction_service import PredictionService
    from signal_bridge.signal_generator import SignalGenerator

    registry = ModelRegistry()
    registry.register(ModelEntry(
        model_id="m-binary", model_version="v1", dataset_id="d1",
        feature_set_id="returns_v1", label_config={}, training_period="",
        validation_period="", test_period="", metrics={}, artifact_path="",
        approval_status="approved", created_at=datetime.now(timezone.utc).isoformat(),
    ))
    features = FeatureRegistry()
    features.register(FeatureSpec("returns", "v1", "pct_change", 1, ["close"]), lambda df: df["close"].pct_change())
    loader = ApprovedModelLoader(registry)
    runtime = FeatureRuntime(features)
    service = PredictionService()
    model = SimpleRuleModel(feature_weights={"returns_v1": 1.0})
    assert set(model.classes_) == {0, 1}
    service.load_model("m-binary", model)
    generator = SignalGenerator(loader, runtime, service)

    result = generator.generate("m-binary", pd.DataFrame({"close": [1.0]}))
    assert result["generated"] is True
    assert result["signal"] == "sell"


def test_repository_default_paper_broker_config_is_explicit_and_ready():
    from paper_broker.readiness import build_paper_broker_readiness

    project_root = Path(__file__).resolve().parents[2]
    report = build_paper_broker_readiness(project_root, config=None, allow_missing=False)

    assert report.status == "READY"
    assert report.mode == "paper"
    assert report.broker_name == "paper_stub"
    assert report.config_path.endswith("examples/paper_broker_config.example.json")


def test_manual_order_rejects_viewer_role(monkeypatch):
    from fastapi.testclient import TestClient
    import core.auth as auth
    from main import app

    monkeypatch.setitem(auth.ROLES, "viewer", "phase30a-viewer-token")
    response = TestClient(app).post(
        "/manual/order",
        headers={"token": "phase30a-viewer-token"},
        json={"symbol": "EURUSD", "direction": "buy", "volume": 1.0},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Operator or admin role required"
