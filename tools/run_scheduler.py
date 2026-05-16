
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler.task_scheduler import TaskScheduler
from scheduler.signal_loop import SignalLoop

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--interval", type=float, default=60.0)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    scheduler = TaskScheduler()
    # Placeholder: real signal loop would be instantiated here
    scheduler.add_interval_task("signal_loop", lambda: print("Tick"), args.interval)
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to stop.")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()
