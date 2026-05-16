
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from live_data.csv_replay_adapter import CSVReplayAdapter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    adapter = CSVReplayAdapter(args.data, speed_multiplier=args.speed)
    adapter.connect()
    ticks = []
    while True:
        tick = adapter.get_latest_tick("EURUSD")
        if not tick:
            break
        ticks.append(tick)
    with open(args.output, "w") as f:
        json.dump(ticks, f, indent=2, default=str)
    print(f"Replayed {len(ticks)} ticks.")

if __name__ == "__main__":
    main()
