#!/usr/bin/env python3
"""CLI: Run local MVP release candidate check.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
Does not make network calls. Does not require real credentials.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import py_compile
import subprocess

from local_app.app_config import load_config
from release_candidate.checklist import (
    build_release_candidate_report,
    render_release_candidate_summary,
    write_release_candidate_report,
)


def _safe_smoke_check(project_root: Path) -> bool:
    """Run safe, fast smoke checks. No network, no credentials, no live trading."""
    modules = [
        "local_app/app_config.py",
        "local_app/operator_status.py",
        "local_app/action_center.py",
        "research_insights/insight_builder.py",
        "paper_runtime/session_journal.py",
        "data_quality/quality_report.py",
        "paper_broker/readiness.py",
        "release_candidate/checklist.py",
    ]
    tools = [
        "tools/run_operator_day.py",
        "tools/show_action_center.py",
        "tools/show_research_insights.py",
        "tools/show_paper_runtime_journal.py",
        "tools/show_data_quality.py",
        "tools/show_paper_broker_readiness.py",
        "tools/run_readiness_audit.py",
        "tools/validate_docs.py",
        "tools/run_release_candidate_check.py",
    ]
    all_ok = True
    for rel in modules + tools:
        path = project_root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as e:
                print(f"[SMOKE FAIL] {rel}: {e}")
                all_ok = False
        else:
            print(f"[SMOKE SKIP] {rel}: file not found")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Run local MVP release candidate check")
    parser.add_argument("--config", required=True, help="Path to config JSON (e.g., examples/local_app_config.example.json)")
    parser.add_argument("--allow-missing", action="store_true", help="Tolerate missing optional docs/tools")
    parser.add_argument("--write-report", action="store_true", help="Write release candidate report to reports/release_candidate/")
    parser.add_argument("--smoke", action="store_true", help="Run safe smoke checks (py_compile, docs validation, build report)")
    args = parser.parse_args()

    print("PAPER-ONLY / DATA-ONLY")
    print("No live trading. No order submission.")
    print("This is not financial advice.")
    print("This does not approve or enable live trading.")
    print("")
    print("Local MVP Release Candidate")
    print("")

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(2)

    config = load_config(config_path)

    # Validate safety flags
    if not config.get("paper_only", True):
        print("ERROR: config.paper_only must be true")
        sys.exit(2)
    if not config.get("data_only", True):
        print("ERROR: config.data_only must be true")
        sys.exit(2)
    if not config.get("no_order_submission", True):
        print("ERROR: config.no_order_submission must be true")
        sys.exit(2)

    report = build_release_candidate_report(PROJECT_ROOT, config=config, allow_missing=args.allow_missing)
    text = render_release_candidate_summary(report)
    print(text)

    if args.smoke:
        smoke_ok = _safe_smoke_check(PROJECT_ROOT)
        if not smoke_ok:
            print("[SMOKE] Some smoke checks failed.")
            if report.status != "BLOCKED":
                report.status = "BLOCKED"
        else:
            print("[SMOKE] All smoke checks passed.")
        print("")

    if args.write_report:
        output_paths = write_release_candidate_report(PROJECT_ROOT, report, config=config)
        for p in output_paths:
            print(f"Written: {p}")
        print("")

    if report.status == "BLOCKED":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
