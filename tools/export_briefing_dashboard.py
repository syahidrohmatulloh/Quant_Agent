#!/usr/bin/env python3
"""CLI: Export briefing dashboard JSON.

Paper-only / data-only.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse

from briefing.briefing_config import load_config, validate_config
from briefing.source_loader import load_sources
from briefing.briefing_builder import build_briefing
from briefing.dashboard_export import export_dashboard_json


def main():
    parser = argparse.ArgumentParser(description="Export briefing dashboard JSON")
    parser.add_argument("--project-root", default=".", help="Project root path")
    parser.add_argument("--config", required=True, help="Path to briefing config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing sources")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print()

    config_path = Path(args.config)
    config = load_config(config_path)
    validation = validate_config(config, allow_missing=args.allow_missing)
    if not validation["valid"]:
        print("Config validation failed:")
        for err in validation["errors"]:
            print(f"  - {err}")
        sys.exit(1)

    loaded = load_sources(config, project_root, allow_missing=args.allow_missing)
    briefing = build_briefing(config, loaded, project_root=project_root)

    outputs = config.get("outputs", {})
    dash_path = project_root / outputs.get("dashboard_json", "reports/dashboard/briefing/latest.json")
    export_dashboard_json(briefing, dash_path)
    print(f"Written: {dash_path}")


if __name__ == "__main__":
    main()
