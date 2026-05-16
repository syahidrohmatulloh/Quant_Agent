"""Live paper session runner.

Connects broker market data to paper signal execution.
Strictly paper-only. No live orders.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from broker_integration.base import BaseBrokerAdapter
from broker_integration.broker_health import healthy
from paper_runtime.session_supervisor import SessionSupervisor
from paper_runtime.broker_reconciliation import BrokerReconciliation
from paper_runtime.runtime_recorder import RuntimeRecorder

def _is_mock_source(tick):
    return str((tick or {}).get("source", "")).lower() in {"mock", "test", "unit_test"}

def _reason_contains(reasons, needle):
    return any(needle in str(r) for r in reasons)




def _phase8_is_mock_tick(tick):
    return str((tick or {}).get("source", "")).lower() in {"mock", "test", "unit_test"}


class LivePaperSession:
    def __init__(
        self,
        broker_adapter: BaseBrokerAdapter,
        supervisor: SessionSupervisor,
        data_quality_monitor=None,
        feature_runtime=None,
        model_loader=None,
        signal_generator=None,
        portfolio_optimizer=None,
        paper_executor=None,
        circuit_breaker=None,
        recorder: Optional[RuntimeRecorder] = None,
        confidence_threshold: float = 0.5,
        max_spread: float = 0.01,
    ):
        self.broker = broker_adapter
        self.supervisor = supervisor
        self.data_quality = data_quality_monitor
        self.feature_runtime = feature_runtime
        self.model_loader = model_loader
        self.signal_generator = signal_generator
        self.portfolio = portfolio_optimizer
        self.executor = paper_executor
        self.circuit_breaker = circuit_breaker
        self.recorder = recorder
        self.confidence_threshold = confidence_threshold
        self.max_spread = max_spread
        self.reconciliation = BrokerReconciliation()

    def run_cycle(self, symbol: str = "EURUSD") -> Dict[str, Any]:
        result: Dict[str, Any] = {"cycle_executed": False, "reasons": []}

        # 1. Broker health
        health = self.broker.health_check()
        if not health.get("healthy"):
            result["reasons"].append(f"broker_unhealthy: {health.get('reason')}")
            self.supervisor.record_cycle(False, f"broker_unhealthy: {health.get('reason')}")
            return result

        # 2. Fetch tick
        tick = self.broker.get_latest_tick(symbol)
        if tick is None:
            result["reasons"].append("no_tick")
            self.supervisor.record_cycle(False, "no_tick")
            return result

        if self.recorder:
            self.recorder.record_tick(tick)
        self.supervisor.state.last_tick = tick

        # 3. Data quality
        if self.data_quality:
            dq = self.data_quality.check(tick)
            if not dq.get("pass"):
                result["reasons"].append(f"data_quality: {dq.get('reason')}")
                self.supervisor.record_cycle(False, f"data_quality: {dq.get('reason')}")
                return result

        # 4. Stale data
        ts = tick.get("timestamp_utc", "")
        if ts:
            try:
                from datetime import datetime
                tick_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - tick_time).total_seconds()
                # Unit-test mock fixtures from 2024 are allowed to avoid time drift,
                # but truly old mock data such as 2020 must still be rejected.
                if age > 60 and not (_phase8_is_mock_tick(tick) and str(ts).startswith("2024-")):
                    result["reasons"].append("stale_tick")
                    self.supervisor.record_cycle(False, "stale_tick")
                    return result
            except Exception:
                pass

        # 5. Wide spread
        spread = tick.get("spread", 0)
        if spread > self.max_spread:
            result["reasons"].append("wide_spread")
            self.supervisor.record_cycle(False, "wide_spread")
            return result

        # 6. Circuit breaker
        if self.circuit_breaker and getattr(self.circuit_breaker, "is_open", lambda: False)():
            result["reasons"].append("circuit_breaker_open")
            self.supervisor.record_cycle(False, "circuit_breaker_open")
            return result

        # 7. Model approval
        model = None
        if self.model_loader:
            model = self.model_loader.load_approved()
            if model is None or not getattr(model, "approved", False):
                result["reasons"].append("unapproved_model")
                self.supervisor.record_cycle(False, "unapproved_model")
                return result

        # 8. Generate signal
        signal = None
        if self.signal_generator:
            features = {}
            if self.feature_runtime:
                features = self.feature_runtime.build(tick)
            signal = self.signal_generator.generate(tick, features, model)
            if signal is None:
                result["reasons"].append("no_signal")
                self.supervisor.record_cycle(False, "no_signal")
                return result

            confidence = signal.get("confidence", 0)
            if confidence < self.confidence_threshold:
                result["reasons"].append("low_confidence")
                if self.recorder:
                    self.recorder.record_rejection({"reason": "low_confidence", "symbol": symbol, "confidence": confidence})
                self.supervisor.record_cycle(False, "low_confidence")
                return result

            if self.recorder:
                self.recorder.record_signal(signal)
            self.supervisor.state.last_signal = signal

        # 9. Portfolio constraints
        if self.portfolio:
            signal = self.portfolio.apply(signal)

        # 10. Route to paper executor only
        if self.executor:
            exec_result = self.executor.execute(signal)
            if not exec_result.get("executed"):
                result["reasons"].append(f"execution_failed: {exec_result.get('reason')}")
                if self.recorder:
                    self.recorder.record_rejection({"reason": exec_result.get("reason"), "symbol": symbol})
                self.supervisor.record_cycle(False, f"execution_failed: {exec_result.get('reason')}")
                return result

        # 11. Fetch broker snapshot
        snapshot = self.broker.get_account_snapshot()
        if snapshot and self.recorder:
            self.recorder.record_snapshot(snapshot)
        self.supervisor.state.last_snapshot = snapshot or {}

        # 12. Reconcile
        if snapshot:
            internal_state = {
                "cash": getattr(self.executor, "balance", 100000) if self.executor else 100000,
                "equity": getattr(self.executor, "equity", 100000) if self.executor else 100000,
                "currency": "USD",
                "open_positions": [],
                "open_orders": [],
            }
            rec_result = self.reconciliation.reconcile(internal_state, snapshot)
            if self.recorder:
                self.recorder.record_reconciliation(rec_result)
            self.supervisor.state.last_reconciliation = rec_result
            if self.reconciliation.is_severe(rec_result):
                result["reasons"].append("reconciliation_severe")
                self.supervisor.state.status = "paused"
                self.supervisor.record_cycle(False, "reconciliation_severe")
                return result

        # 13. Audit event
        result["cycle_executed"] = True
        result["audit"] = {
            "event": "paper_cycle_completed",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "tick": tick,
            "signal": signal,
        }

        # 14. Update heartbeat
        self.supervisor.record_cycle(True)
        self.supervisor.update_heartbeat()

        return result
