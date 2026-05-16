#!/usr/bin/env python3
"""Collect OANDA practice market data for multiple symbols."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker_integration.broker_config import BrokerConfig, BrokerConfigError
from broker_integration.oanda.oanda_streaming import OandaPollingStream
from streaming.stream_recorder import StreamRecorder


def main():
    parser = argparse.ArgumentParser(description="Collect OANDA market data")
    parser.add_argument("--config", required=True, help="OANDA config JSON")
    parser.add_argument("--symbols", nargs="+", default=["EUR_USD"], help="Symbols to collect")
    parser.add_argument("--poll-interval", type=int, default=5, help="Poll interval seconds")
    parser.add_argument("--duration-seconds", type=int, default=300, help="Collection duration")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    try:
        config = BrokerConfig(**cfg)
    except BrokerConfigError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    import time
    start = time.time()
    recorder = StreamRecorder(args.output, "oanda-collection")

    for symbol in args.symbols:
        stream = OandaPollingStream(
            config,
            poll_interval_seconds=args.poll_interval,
            max_events=args.duration_seconds // max(args.poll_interval, 1),
        )
        for event in stream.start(symbol):
            if time.time() - start > args.duration_seconds:
                stream.stop()
                break
            if event.get("event_type") == "tick":
                recorder.record_tick(event)
            else:
                recorder.record_event(event)

    recorder.flush()
    print(f"Collection complete. Output: {recorder.output_dir}")


if __name__ == "__main__":
    main()
