
import argparse
import shutil
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-backup", required=True)
    parser.add_argument("--audit-backup", required=True)
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)
    shutil.copy2(args.db_backup, "data/quant_platform.db")
    shutil.copy2(args.audit_backup, "data/audit.jsonl")
    print("Restore complete.")

if __name__ == "__main__":
    main()
