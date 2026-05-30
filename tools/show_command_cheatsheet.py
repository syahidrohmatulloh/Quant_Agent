#!/usr/bin/env python3
"""CLI: show command cheat sheet.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from docs_tools.command_examples import get_command_examples
except ModuleNotFoundError:
    get_command_examples = None


def main():
    parser = argparse.ArgumentParser(description="Show command cheat sheet")
    parser.add_argument("--summary", action="store_true", help="Show categories only")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")

    ce = get_command_examples() if get_command_examples is not None else None

    if args.summary:
        print("Command Categories")
        print("=" * 40)
        if ce is not None:
            for category in ce.examples:
                print("- " + category)
        else:
            cheatsheet_path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
            if cheatsheet_path.exists():
                for line in cheatsheet_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("#"):
                        print("- " + line.lstrip("#").strip())
            else:
                print("- Commands")
    else:
        cheatsheet_path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
        if cheatsheet_path.exists():
            print(cheatsheet_path.read_text(encoding="utf-8"))
        else:
            # Fallback to programmatic examples
            if ce is not None:
                for category, commands in ce.examples.items():
                    print("## " + category)
                    for cmd in commands:
                        print(cmd)
                    print()
            else:
                print("# Commands")
                print()
                print("python3 -m pytest tests/ -q")

    sys.exit(0)


if __name__ == "__main__":
    main()
