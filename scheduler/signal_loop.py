
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from live_data.base_adapter import BaseMarketDataAdapter
from live_data.data_quality_monitor import DataQualityMonitor
from live_data.market_clock import MarketClock
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from signal_bridge.signal_generator import SignalGenerator
from signal_bridge.signal_router import SignalRouter
from signal_bridge.paper_signal_executor import PaperSignalExecutor
from portfolio_optimization.allocation_engine import AllocationEngine
from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting
from monitoring.signal_monitor import SignalMonitor
from storage.audit import AuditLogger

class SignalLoop:
    def __init__(self,
                 data_adapter: BaseMarketDataAdapter,
                 data_quality: DataQualityMonitor,
                 market_clock: MarketClock,
                 model_loader: ApprovedModelLoader,
                 feature_runtime: FeatureRuntime,
                 prediction_service: PredictionService,
                 signal_generator: SignalGenerator,
                 signal_router: SignalRouter,
                 paper_executor: PaperSignalExecutor,
                 allocation_engine: Optional[Any] = None,
                 live_metrics: Optional[LiveMetrics] = None,
                 alerting: Optional[Alerting] = None,
                 audit: Optional[AuditLogger] = None,
                 min_confidence: float = 0.5):
        self.data_adapter = data_adapter
        self.data_quality = data_quality
        self.market_clock = market_clock
        self.model_loader = model_loader
        self.feature_runtime = feature_runtime
        self.prediction_service = prediction_service
        self.signal_generator = signal_generator
        self.signal_router = signal_router
        self.paper_executor = paper_executor
        self.allocation_engine = allocation_engine
        self.live_metrics = live_metrics or LiveMetrics()
        self.alerting = alerting or Alerting()
        self.audit = audit
        self.min_confidence = min_confidence
        self._rejected_signals: list = []

    def run_cycle(self, symbol: str = "EURUSD") -> Dict[str, Any]:
        cycle_id = str(uuid.uuid4())
        result = {"cycle_id": cycle_id, "timestamp": datetime.now(timezone.utc).isoformat(), "executed": False}

        # 1. System health
        if self.paper_executor.circuit_breaker:
            result["reason"] = "circuit_breaker_open"
            self._log_rejection(cycle_id, "circuit_breaker_open")
            return result

        # 2. Market clock
        if not self.market_clock.is_trading_window():
            result["reason"] = "market_closed"
            self._log_rejection(cycle_id, "market_closed")
            return result

        # 3. Pull data
        tick = self.data_adapter.get_latest_tick(symbol)
        if not tick:
            result["reason"] = "no_data"
            self._log_rejection(cycle_id, "no_data")
            return result

        # 4. Data quality
        issues = self.data_quality.check_tick(tick)
        if issues:
            result["reason"] = "data_quality_failed"
            result["issues"] = issues
            self._log_rejection(cycle_id, "data_quality_failed", details=issues)
            return result

        # 5. Load approved model
        approved_models = self.model_loader.list_approved()
        if not approved_models:
            result["reason"] = "no_approved_model"
            self._log_rejection(cycle_id, "no_approved_model")
            return result
        model = approved_models[0]

        # 6. Build features
        import pandas as pd
        df = pd.DataFrame([tick])
        feat_result = self.feature_runtime.compute(df, model.feature_set_id)
        if not feat_result or not feat_result.get("valid"):
            result["reason"] = "feature_runtime_failed"
            self._log_rejection(cycle_id, "feature_runtime_failed")
            return result

        # 7. Predict
        feat_df = pd.DataFrame([feat_result["feature_vector"]])
        pred = self.prediction_service.predict(model.model_id, feat_df)
        if pred.get("error"):
            result["reason"] = "prediction_failed"
            self._log_rejection(cycle_id, "prediction_failed")
            return result

        # 8. Confidence check
        if pred.get("confidence", 0) < self.min_confidence:
            result["reason"] = "low_confidence"
            result["confidence"] = pred.get("confidence")
            self._log_rejection(cycle_id, "low_confidence", details={"confidence": pred.get("confidence")})
            return result

        # 9. Generate signal
        signal = self.signal_generator.generate(model.model_id, df)
        if not signal.get("generated"):
            result["reason"] = signal.get("reason", "signal_generation_failed")
            self._log_rejection(cycle_id, result["reason"])
            return result

        # 10. Route
        routed = self.signal_router.route(signal)
        if not routed.get("routed"):
            result["reason"] = "routing_failed"
            self._log_rejection(cycle_id, "routing_failed")
            return result

        # 11. Portfolio allocation (optional)
        if self.allocation_engine:
            # Simplified: just pass through
            pass

        # 12. Paper execute
        exec_result = self.paper_executor.execute(routed)
        if exec_result.get("executed"):
            result["executed"] = True
            result["broker_order_id"] = exec_result.get("broker_order_id")
            result["destination"] = "paper"
            self.live_metrics.record_signal(True)
        else:
            result["reason"] = exec_result.get("reason", "execution_failed")
            self._log_rejection(cycle_id, result["reason"])

        return result

    def _log_rejection(self, cycle_id: str, reason: str, details: Optional[Dict] = None):
        self.live_metrics.record_signal(False, reason)
        if self.audit:
            self.audit.log("signal_rejected", cycle_id, "system", "system", {"reason": reason, "details": details or {}})
        self._rejected_signals.append({"cycle_id": cycle_id, "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()})

    def get_rejected_signals(self, limit: int = 50) -> list:
        return self._rejected_signals[-limit:]
