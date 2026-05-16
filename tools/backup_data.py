
import argparse
import shutil
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    for src in ["data/quant_platform.db", "data/audit.jsonl"]:
        if os.path.exists(src):
            dst = os.path.join(args.output, f"{os.path.basename(src)}_{date_str}")
            shutil.copy2(src, dst)
            print(f"Backed up {src} -> {dst}")
    print("Backup complete.")

if __name__ == "__main__":
    main()
