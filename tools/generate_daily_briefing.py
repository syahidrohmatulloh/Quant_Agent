#!/usr/bin/env python3
"""CLI: Generate daily briefing (Markdown + JSON + alert summary + log).

Paper-only / data-only. No live trading. No order submission.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json

from briefing.briefing_config import load_config, validate_config
from briefing.source_loader import load_sources
from briefing.briefing_builder import build_briefing
from briefing.briefing_report import write_markdown_report, write_json_report, write_alert_summary
from briefing.briefing_log import append_briefing_log


def main():
    parser = argparse.ArgumentParser(description="Generate daily briefing")
    parser.add_argument("--project-root", default=".", help="Project root path")
    parser.add_argument("--config", required=True, help="Path to briefing config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing sources")
    args = parser.parse_args()

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

    project_root = Path(args.project_root).resolve()
    loaded = load_sources(config, project_root, allow_missing=args.allow_missing)

    # Try to load previous signals from latest briefing log for change detection
    previous_signals = None
    log_path = project_root / config.get("outputs", {}).get("briefing_log", "reports/briefing/briefing_log.jsonl")
    if log_path.exists():
        # We don't parse log for signals; change detection is based on experiment summary
        pass

    briefing = build_briefing(config, loaded, previous_signals=previous_signals, project_root=project_root)

    outputs = config.get("outputs", {})

    # Markdown
    md_path = project_root / outputs.get("briefing_markdown", "reports/briefing/daily_briefing.md")
    write_markdown_report(briefing, md_path)
    print(f"Written: {md_path}")

    # JSON
    json_path = project_root / outputs.get("briefing_json", "reports/briefing/daily_briefing.json")
    write_json_report(briefing, json_path)
    print(f"Written: {json_path}")

    # Alert summary
    alert_path = project_root / outputs.get("alert_summary_json", "reports/briefing/alert_summary.json")
    write_alert_summary(briefing, alert_path)
    print(f"Written: {alert_path}")

    # Log
    log_path = project_root / outputs.get("briefing_log", "reports/briefing/briefing_log.jsonl")
    append_briefing_log(briefing, log_path)
    print(f"Appended: {log_path}")

    print()
    print(f"Briefing generated: {briefing['summary']['headline']}")
    print(f"Alerts: {briefing['summary']['alert_count']} (C:{briefing['summary']['critical_count']} W:{briefing['summary']['warning_count']} I:{briefing['summary']['info_count']})")


if __name__ == "__main__":
    main()
