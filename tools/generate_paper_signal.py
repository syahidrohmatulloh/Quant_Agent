
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from signal_bridge.signal_generator import SignalGenerator
from signal_bridge.approved_model_loader import ApprovedModelLoader
from signal_bridge.feature_runtime import FeatureRuntime
from signal_bridge.prediction_service import PredictionService
from research_pipeline.model_registry import ModelRegistry
from research_pipeline.feature_registry import FeatureRegistry
from research_pipeline.model_trainer import SimpleRuleModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--features", required=True, help="JSON file with latest features data")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # Load minimal registry for demo
    registry = ModelRegistry()
    # (In real use, load from persistent storage)
    loader = ApprovedModelLoader(registry)
    freg = FeatureRegistry()
    runtime = FeatureRuntime(freg)
    svc = PredictionService()
    gen = SignalGenerator(loader, runtime, svc)

    with open(args.features, "r") as f:
        data = json.load(f)
    import pandas as pd
    df = pd.DataFrame(data)
    result = gen.generate(args.model_id, df)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print("Signal generated:", result.get("signal_id"))

if __name__ == "__main__":
    main()
