#!/usr/bin/env python3
"""Stream OANDA practice prices."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_streaming import OandaPollingStream
from streaming.stream_recorder import StreamRecorder
from streaming.stream_supervisor import StreamSupervisor


def main():
    parser = argparse.ArgumentParser(description="Stream OANDA practice prices")
    parser.add_argument("--config", required=True, help="OANDA config JSON")
    parser.add_argument("--symbol", default="EUR_USD", help="Instrument symbol")
    parser.add_argument("--max-events", type=int, default=100, help="Max events to collect")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--real-network", action="store_true", help="Use real network (requires credentials)")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if args.real_network and not config.api_key:
        print(json.dumps({"error": "missing_credentials", "message": "Set OANDA_API_KEY env var for real network"}))
        sys.exit(1)

    supervisor = StreamSupervisor(stream_id="oanda-stream-001")
    recorder = StreamRecorder(args.output, "oanda-stream-001")
    stream = OandaPollingStream(
        config,
        poll_interval_seconds=1.0 if args.real_network else 0.01,
        max_events=args.max_events,
    )

    supervisor.start()
    for event in stream.start(args.symbol):
        if event.get("event_type") == "tick":
            recorder.record_tick(event)
        elif event.get("event_type") == "error":
            recorder.record_error(event)
            supervisor.record_error(event.get("error", ""))
        else:
            recorder.record_event(event)
            supervisor.record_event()
    supervisor.stop()
    recorder.flush()

    print(json.dumps({
        "events": stream.event_count,
        "output": recorder.output_dir,
        "supervisor": supervisor.status(),
    }, indent=2))


if __name__ == "__main__":
    main()
