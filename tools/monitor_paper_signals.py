
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from monitoring.live_metrics import LiveMetrics
from monitoring.alerting import Alerting
from monitoring.signal_monitor import SignalMonitor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.metrics_file, "r") as f:
        raw = json.load(f)

    metrics = LiveMetrics()
    metrics.signals_generated = raw.get("signals_generated", 0)
    metrics.signals_rejected = raw.get("signals_rejected", 0)
    metrics.current_drawdown = raw.get("drawdown", 0)

    alerting = Alerting()
    monitor = SignalMonitor(metrics, alerting)
    alerts = monitor.check_alerts()

    out = {
        "metrics": metrics.summary(),
        "alerts": [{"level": a.level, "category": a.category, "message": a.message} for a in alerts]
    }
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print("Monitoring report saved to", args.output)

if __name__ == "__main__":
    main()
