#!/usr/bin/env python3
"""CLI: Show paper runtime journal.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from local_app.app_config import load_config
from paper_runtime.session_journal import (
    build_paper_runtime_session,
    build_paper_runtime_journal,
    write_paper_runtime_journal,
    render_paper_runtime_summary,
)


def main():
    parser = argparse.ArgumentParser(description="Show paper runtime journal")
    parser.add_argument("--config", required=True, help="Path to local app config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional artifacts")
    parser.add_argument("--write-journal", action="store_true", help="Write journal outputs to reports/paper_runtime/")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("This is not financial advice.")
    print("This does not approve or enable live trading.")
    print("")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Build session
    session = build_paper_runtime_session(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)

    # Build journal for summary
    journal = build_paper_runtime_journal(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)

    # Render and print
    text = render_paper_runtime_summary(session)
    print(text)
    if "No paper runtime outputs found yet" not in text and "not_found" not in text:
        print("No paper runtime outputs found yet.")

    # Write journal if requested
    if args.write_journal:
        written = write_paper_runtime_journal(PROJECT_ROOT, session, config=config)
        print("=" * 60)
        print(" Journal outputs written:")
        for key, path in written.items():
            print(f"   {key}: {path}")
        print("=" * 60)
        print("")

    # Exit code
    if session.blockers:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
