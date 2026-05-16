
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    snapshot = {
        "timestamp": "",
        "mode": "paper",
        "positions": [],
        "signals": [],
        "alerts": []
    }
    with open(args.output, "w") as f:
        json.dump(snapshot, f, indent=2)
    print("Snapshot saved to", args.output)

if __name__ == "__main__":
    main()
