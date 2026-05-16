
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_pipeline.model_registry import ModelRegistry, ModelEntry
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="JSON config for model entry")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        cfg = json.load(f)

    registry = ModelRegistry()
    entry = ModelEntry(
        model_id=cfg["model_id"],
        model_version=cfg["model_version"],
        dataset_id=cfg["dataset_id"],
        feature_set_id=cfg["feature_set_id"],
        label_config=cfg["label_config"],
        training_period=cfg["training_period"],
        validation_period=cfg["validation_period"],
        test_period=cfg["test_period"],
        metrics=cfg["metrics"],
        artifact_path=cfg["artifact_path"],
        approval_status="draft",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    registry.register(entry)

    with open(args.output, "w") as f:
        json.dump(registry.to_dict(), f, indent=2, default=str)
    print("Model registered:", cfg["model_id"])

if __name__ == "__main__":
    main()
