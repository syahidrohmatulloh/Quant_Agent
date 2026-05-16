
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--paper-only", action="store_true", default=True)
    args = parser.parse_args()
    with open(args.config, "r") as f:
        config = json.load(f)
    print("Signal bridge running (paper-only:", args.paper_only, ")")
    print("Config:", config)

if __name__ == "__main__":
    main()
