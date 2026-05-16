
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_pipeline.model_evaluator import ModelEvaluator
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--y-true", required=True, help="CSV with true labels")
    parser.add_argument("--y-pred", required=True, help="CSV with predictions")
    parser.add_argument("--out-of-sample", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    y_true = pd.read_csv(args.y_true).iloc[:, 0]
    y_pred = pd.read_csv(args.y_pred).iloc[:, 0].values

    evaluator = ModelEvaluator()
    result = evaluator.evaluate(y_true, y_pred, out_of_sample=args.out_of_sample)

    out = {
        "accuracy": result.accuracy,
        "precision": result.precision,
        "recall": result.recall,
        "f1": result.f1,
        "confusion_matrix": result.confusion_matrix,
        "overfitting_warning": result.overfitting_warning,
        "out_of_sample": result.out_of_sample
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("Evaluation saved to", args.output)

if __name__ == "__main__":
    main()
