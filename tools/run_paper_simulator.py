"""Run paper simulator engine.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_simulator.simulator_engine import SimulatorEngine
from paper_simulator.simulator_config import load_simulator_config


def main():
    parser = argparse.ArgumentParser(description="Run paper simulator engine.")
    parser.add_argument("--config", required=True, help="Path to simulator config JSON.")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing CSV paths.")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    config, ok, errors, warnings = load_simulator_config(args.config)
    if not ok:
        print("Config validation FAILED:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)

    for w in warnings:
        print("  WARN:  " + w)

    # Load decisions from paper_decision_log if exists
    decisions = []
    decision_log = config.get("paper_decision_log")
    if decision_log and Path(decision_log).exists():
        with open(decision_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    decisions.append(json.loads(line))

    engine = SimulatorEngine(config)
    summary = engine.run(decisions)

    print("Simulation complete.")
    print("  Decisions processed: " + str(summary["decisions_processed"]))
    print("  Fills simulated:     " + str(summary["fills_simulated"]))
    print("  Positions count:     " + str(summary["positions_count"]))
    if summary["warnings"]:
        print("  Warnings:")
        for w in summary["warnings"]:
            print("    " + w)


if __name__ == "__main__":
    main()
