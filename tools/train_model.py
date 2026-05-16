
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_pipeline.model_trainer import ModelTrainer
from research_pipeline.label_builder import LabelBuilder, LabelConfig
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="CSV with features and target column")
    parser.add_argument("--target", default="target")
    parser.add_argument("--model-type", default="simple_rule")
    parser.add_argument("--model-id", default="model_001")
    parser.add_argument("--model-version", default="v1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    y = df[args.target]
    X = df.drop(columns=[args.target])

    trainer = ModelTrainer(model_type=args.model_type)
    result = trainer.train(X, y, model_id=args.model_id, model_version=args.model_version)

    out = {
        "model_id": result.model_id,
        "model_version": result.model_version,
        "predictions": result.predictions.tolist()[:10],
        "confidence": result.confidence.tolist()[:10]
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("Model trained:", args.model_id)

if __name__ == "__main__":
    main()
