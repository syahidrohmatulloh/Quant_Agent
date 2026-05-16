"""Deterministic paper trading session runner using CSV replay data."""
import os
import sys
import json
import csv
import uuid
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.audit import AuditLogger
from storage.db import SQLiteStore
from scheduler.heartbeat import Heartbeat
from live_data.csv_replay_adapter import CSVReplayAdapter
from live_data.data_quality_monitor import DataQualityMonitor
from live_data.market_clock import MarketClock
from live_data.data_normalizer import DataNormalizer
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from signal_bridge.signal_generator import SignalGenerator
from signal_bridge.signal_router import SignalRouter
from signal_bridge.paper_signal_executor import PaperSignalExecutor
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from research_pipeline.feature_registry import FeatureRegistry, FeatureSpec
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting
from monitoring.signal_monitor import SignalMonitor
from portfolio_optimization.allocation_engine import AllocationEngine
import pandas as pd


class PaperSessionRunner:
    """Runs a deterministic paper trading session over replay data."""

    def __init__(self,
                 replay_path: str,
                 model_config: Dict[str, Any],
                 signal_loop_config: Dict[str, Any],
                 starting_balance: float = 100000.0,
                 symbols: List[str] = None,
                 timeframe: str = "1m",
                 max_cycles: int = 100,
                 output_dir: str = "reports/session_001",
                 min_confidence: float = 0.5):
        self.replay_path = replay_path
        self.model_config = model_config
        self.signal_loop_config = signal_loop_config
        self.starting_balance = starting_balance
        self.symbols = symbols or ["EURUSD"]
        self.timeframe = timeframe
        self.max_cycles = max_cycles
        self.output_dir = output_dir
        self.min_confidence = min_confidence
        self.trades: List[Dict[str, Any]] = []
        self.signals: List[Dict[str, Any]] = []
        self.rejected_signals: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.session_id = str(uuid.uuid4())
        self._heartbeat = Heartbeat(component="paper_session")

    def _setup(self):
        os.makedirs(self.output_dir, exist_ok=True)
        self._audit_path = os.path.join(self.output_dir, "audit.jsonl")
        self._db_path = os.path.join(self.output_dir, "session.db")
        self.broker = PaperBroker(
            balance=self.starting_balance,
            commission_per_lot=7.0,
            slippage_pips=0.5,
            leverage=100.0
        )
        self.risk = RiskManager(max_exposure=10.0)
        self.audit = AuditLogger(self._audit_path)
        self.store = SQLiteStore(self._db_path)
        self.adapter = CSVReplayAdapter(self.replay_path)
        self.adapter.connect()
        self.data_quality = DataQualityMonitor()
        self.market_clock = MarketClock()
        self.mreg = ModelRegistry()
        self._register_model()
        self.loader = ApprovedModelLoader(self.mreg)
        self.freg = FeatureRegistry()
        self._register_features()
        self.fr = FeatureRuntime(self.freg, min_lookback=2)
        self.ps = PredictionService()
        self._load_prediction_model()
        self.sg = SignalGenerator(self.loader, self.fr, self.ps)
        self.router = SignalRouter(paper_only=True)
        self.executor = PaperSignalExecutor(
            broker=self.broker,
            risk_manager=self.risk,
            audit=self.audit,
            max_signals_per_minute=100,
            circuit_breaker=False
        )
        self.metrics = LiveMetrics()
        self.alerting = Alerting()
        self.monitor = SignalMonitor(self.metrics, self.alerting)
        self.allocation = AllocationEngine()

    def _register_model(self):
        cfg = self.model_config
        entry = ModelEntry(
            model_id=cfg["model_id"],
            model_version=cfg.get("model_version", "v1"),
            dataset_id=cfg.get("dataset_id", "ds-001"),
            feature_set_id=cfg.get("feature_set_id", "sma_v1"),
            label_config=cfg.get("label_config", {"horizon": 10}),
            training_period=cfg.get("training_period", "2023-01-01/2023-06-01"),
            validation_period=cfg.get("validation_period", "2023-06-01/2023-09-01"),
            test_period=cfg.get("test_period", "2023-09-01/2023-12-01"),
            metrics=cfg.get("metrics", {"accuracy": 0.55}),
            artifact_path=cfg.get("artifact_path", ""),
            approval_status=cfg.get("approval_status", "approved"),
            created_at=datetime.now(timezone.utc).isoformat(),
            approved_by=cfg.get("approved_by", "session"),
            approval_notes=cfg.get("approval_notes", "")
        )
        self.mreg.register(entry)

    def _register_features(self):
        def mock_sma(df):
            return df["close"].rolling(window=2).mean()
        self.freg.register(
            FeatureSpec("sma", "v1", "mock_sma", 2, ["close"]),
            mock_sma
        )

    def _load_prediction_model(self):
        from research_pipeline.model_trainer import SimpleRuleModel
        self.ps.load_model(self.model_config["model_id"], SimpleRuleModel())

    def run(self) -> Dict[str, Any]:
        self._setup()
        cycles_run = 0
        for i in range(self.max_cycles):
            if not self.adapter.is_connected():
                break
            symbol = self.symbols[i % len(self.symbols)]
            cycle_result = self._run_cycle(symbol, i)
            cycles_run += 1
            self._heartbeat.beat(status="ok", metadata={"cycle": i, "symbol": symbol})
            if cycle_result.get("executed"):
                self.trades.append(cycle_result)
            elif cycle_result.get("reason"):
                self.rejected_signals.append(cycle_result)
            self.signals.append(cycle_result)
            # Update prices for open positions
            tick = cycle_result.get("tick")
            if tick:
                self.broker.update_prices(symbol, tick.get("bid", 1.0), tick.get("ask", 1.0))
        return self._finalize(cycles_run)

    def _run_cycle(self, symbol: str, cycle_num: int) -> Dict[str, Any]:
        cycle_id = str(uuid.uuid4())
        result = {
            "cycle_id": cycle_id,
            "cycle_num": cycle_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "executed": False
        }
        # Pull replay data
        tick = self.adapter.get_latest_tick(symbol)
        if not tick:
            result["reason"] = "no_data"
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "no_data"})
            return result
        result["tick"] = tick
        # Validate data quality
        issues = self.data_quality.check_tick(tick)
        if issues:
            result["reason"] = "data_quality_failed"
            result["issues"] = issues
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "data_quality", "issues": issues})
            return result
        # Market clock
        if not self.market_clock.is_trading_window():
            result["reason"] = "market_closed"
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "market_closed"})
            return result
        # Build features
        df = pd.DataFrame([tick])
        feat = self.fr.compute(df, self.model_config.get("feature_set_id", "sma_v1"))
        if not feat or not feat.get("valid"):
            result["reason"] = "feature_runtime_failed"
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "feature_runtime_failed"})
            return result
        # Generate signal
        signal = self.sg.generate(self.model_config["model_id"], df)
        self.monitor.on_signal(signal)
        if not signal.get("generated"):
            result["reason"] = signal.get("reason", "signal_generation_failed")
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": result["reason"]})
            return result
        # Route
        routed = self.router.route(signal)
        if not routed.get("routed"):
            result["reason"] = "routing_failed"
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "routing_failed"})
            return result
        # Risk
        risk_decision = self.risk.evaluate(symbol, signal.get("signal", "hold"), 1.0)
        if not risk_decision.allowed:
            result["reason"] = "risk_rejected"
            result["risk_decision_id"] = risk_decision.risk_decision_id
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": "risk_rejected", "risk_decision_id": risk_decision.risk_decision_id})
            return result
        # Paper execute
        exec_result = self.executor.execute(routed)
        self.monitor.on_order(exec_result)
        if exec_result.get("executed"):
            result["executed"] = True
            result["broker_order_id"] = exec_result.get("broker_order_id")
            result["broker_position_id"] = exec_result.get("broker_position_id")
            result["destination"] = "paper"
            self.audit.log("paper_order_created", cycle_id, "system", "system", {
                "order_id": exec_result.get("broker_order_id"),
                "position_id": exec_result.get("broker_position_id"),
                "symbol": symbol
            })
        else:
            result["reason"] = exec_result.get("reason", "execution_failed")
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": result["reason"]})
        return result

    def _finalize(self, cycles_run: int) -> Dict[str, Any]:
        # Write outputs
        self._write_csv("trades.csv", self.trades, ["cycle_id", "cycle_num", "timestamp", "symbol", "executed", "broker_order_id", "broker_position_id", "destination"])
        self._write_csv("signals.csv", self.signals, ["cycle_id", "cycle_num", "timestamp", "symbol", "executed", "reason"])
        self._write_csv("rejected_signals.csv", self.rejected_signals, ["cycle_id", "cycle_num", "timestamp", "symbol", "reason"])
        # Alerts
        alerts = self.monitor.check_alerts()
        self.alerts = [{"level": a.level, "category": a.category, "message": a.message, "timestamp": a.timestamp, "value": a.value} for a in alerts]
        with open(os.path.join(self.output_dir, "alerts.json"), "w") as f:
            json.dump(self.alerts, f, indent=2, default=str)
        # Session summary
        summary = {
            "session_id": self.session_id,
            "cycles_run": cycles_run,
            "signals_generated": len([s for s in self.signals if s.get("executed")]),
            "signals_rejected": len(self.rejected_signals),
            "trades_count": len(self.trades),
            "starting_balance": self.starting_balance,
            "current_balance": self.broker.balance,
            "open_positions": len([p for p in self.broker.positions.values() if p.status == "open"]),
            "closed_positions": len([p for p in self.broker.positions.values() if p.status == "closed"]),
            "realized_pnl": sum(p.realized_pnl for p in self.broker.positions.values()),
            "unrealized_pnl": sum(p.unrealized_pnl for p in self.broker.positions.values() if p.status == "open"),
            "paper_only": True,
            "model_id": self.model_config.get("model_id"),
            "model_approval_status": self.model_config.get("approval_status", "approved"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        with open(os.path.join(self.output_dir, "session_summary.json"), "w") as f:
            json.dump(summary, f, indent=2, default=str)
        # Audit validation
        audit_validation = self._validate_audit()
        with open(os.path.join(self.output_dir, "audit_validation.json"), "w") as f:
            json.dump(audit_validation, f, indent=2, default=str)
        return summary

    def _write_csv(self, filename: str, rows: List[Dict[str, Any]], fieldnames: List[str]):
        if not rows:
            return
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def _validate_audit(self) -> Dict[str, Any]:
        from runtime_validation.audit_validator import AuditRuntimeValidator
        validator = AuditRuntimeValidator(self._audit_path, self._db_path)
        return validator.validate()


def run_paper_session(replay_path: str,
                      config_path: str,
                      cycles: int = 100,
                      output_dir: str = "reports/session_001") -> Dict[str, Any]:
    with open(config_path, "r") as f:
        config = json.load(f)
    runner = PaperSessionRunner(
        replay_path=replay_path,
        model_config=config["model"],
        signal_loop_config=config.get("signal_loop", {}),
        starting_balance=config.get("starting_balance", 100000.0),
        symbols=config.get("symbols", ["EURUSD"]),
        timeframe=config.get("timeframe", "1m"),
        max_cycles=cycles,
        output_dir=output_dir,
        min_confidence=config.get("min_confidence", 0.5)
    )
    return runner.run()
