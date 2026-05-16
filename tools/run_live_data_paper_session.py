#!/usr/bin/env python3
"""Run a live data paper trading session."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_practice_adapter import OandaPracticeAdapter
from broker_integration.alpaca.alpaca_paper_adapter import AlpacaPaperAdapter
from broker_integration.ibkr.ibkr_paper_adapter import IbkrPaperAdapter
from paper_runtime.live_paper_session import LivePaperSession
from paper_runtime.session_supervisor import SessionSupervisor
from paper_runtime.runtime_recorder import RuntimeRecorder

ADAPTERS = {
    "oanda": OandaPracticeAdapter,
    "alpaca": AlpacaPaperAdapter,
    "ibkr": IbkrPaperAdapter,
}


def main():
    parser = argparse.ArgumentParser(description="Run live data paper session")
    parser.add_argument("--config", required=True, help="Session config JSON")
    parser.add_argument("--cycles", type=int, default=10, help="Number of cycles")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    broker_cfg = cfg.get("broker", {})
    broker_name = broker_cfg.get("broker_name", "unknown")

    try:
        config = BrokerConfig(**broker_cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    adapter_cls = ADAPTERS.get(broker_name)
    if adapter_cls is None:
        print(json.dumps({"error": "unsupported_broker"}))
        sys.exit(1)

    adapter = adapter_cls(config)
    session_id = cfg.get("session_id", "default")
    supervisor = SessionSupervisor(session_id=session_id)
    recorder = RuntimeRecorder(args.output, session_id)
    session = LivePaperSession(adapter, supervisor, recorder=recorder)

    supervisor.start()
    for i in range(args.cycles):
        result = session.run_cycle(cfg.get("symbol", "EURUSD"))
        print(f"Cycle {i+1}/{args.cycles}: executed={result['cycle_executed']}")
        if supervisor.state.status == "paused":
            print("Session paused due to severe reconciliation mismatch.")
            break
        if supervisor.state.status == "error":
            print("Session stopped due to max failures.")
            break
    supervisor.stop()

    print(f"Session complete. Output: {recorder.output_dir}")


if __name__ == "__main__":
    main()
