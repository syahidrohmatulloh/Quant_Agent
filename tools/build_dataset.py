
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research_pipeline.dataset_builder import DatasetBuilder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file with OHLCV data")
    parser.add_argument("--source", default="ohlcv")
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--output", required=True, help="Output JSON for dataset metadata")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    builder = DatasetBuilder()
    meta = builder.build(data, source=args.source, timeframe=args.timeframe)

    with open(args.output, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print("Dataset built:", meta["dataset_id"])
    print("Rows:", meta["row_count"])

if __name__ == "__main__":
    main()
