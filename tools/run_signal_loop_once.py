
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler.signal_loop import SignalLoop
from live_data.csv_replay_adapter import CSVReplayAdapter
from live_data.data_quality_monitor import DataQualityMonitor
from live_data.market_clock import MarketClock
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from signal_bridge.signal_generator import SignalGenerator
from signal_bridge.signal_router import SignalRouter
from signal_bridge.paper_signal_executor import PaperSignalExecutor
from core.paper_broker import PaperBroker
from core.risk import RiskManager
from storage.audit import AuditLogger
from research_pipeline.model_registry import ModelRegistry
from research_pipeline.feature_registry import FeatureRegistry

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="CSV/JSON market data file")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    adapter = CSVReplayAdapter(args.data)
    adapter.connect()
    loop = SignalLoop(
        data_adapter=adapter,
        data_quality=DataQualityMonitor(),
        market_clock=MarketClock(),
        model_loader=ApprovedModelLoader(ModelRegistry()),
        feature_runtime=FeatureRuntime(FeatureRegistry()),
        prediction_service=PredictionService(),
        signal_generator=SignalGenerator(
            ApprovedModelLoader(ModelRegistry()),
            FeatureRuntime(FeatureRegistry()),
            PredictionService()
        ),
        signal_router=SignalRouter(),
        paper_executor=PaperSignalExecutor(
            PaperBroker(), RiskManager(), AuditLogger()
        )
    )
    result = loop.run_cycle(args.symbol)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print("Cycle result:", result)

if __name__ == "__main__":
    main()
