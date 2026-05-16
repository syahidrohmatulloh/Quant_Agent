
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_pipeline.drift_monitor import DriftMonitor
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, help="CSV reference features")
    parser.add_argument("--current", required=True, help="CSV current features")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    ref = pd.read_csv(args.reference)
    cur = pd.read_csv(args.current)

    monitor = DriftMonitor(ref)
    report = monitor.check(cur)

    out = {
        "feature_drift": report.feature_drift,
        "prediction_drift": report.prediction_drift,
        "performance_drift": report.performance_drift,
        "data_quality": report.data_quality,
        "missing_rate": report.missing_rate,
        "spread_regime": report.spread_regime,
        "alert": report.alert
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("Drift check saved to", args.output)
    if report.alert:
        print("ALERT: Drift detected!")

if __name__ == "__main__":
    main()
