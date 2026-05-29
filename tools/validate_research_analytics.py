#!/usr/bin/env python3
"""Validate Phase 17 research analytics modules and tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import importlib
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODULES = [
    "research_analytics.performance_metrics",
    "research_analytics.drawdown_analysis",
    "research_analytics.signal_quality",
    "research_analytics.regime_attribution",
    "research_analytics.strategy_attribution",
    "research_analytics.stability_analysis",
    "research_analytics.comparison_report",
    "research_analytics.analytics_export",
    "research_analytics.research_config",
]

TOOLS = [
    "tools.validate_research_config",
    "tools.run_research_analytics",
    "tools.analyze_strategy_performance",
    "tools.analyze_signal_quality",
    "tools.analyze_regime_attribution",
    "tools.compare_research_results",
    "tools.export_research_dashboard",
    "tools.validate_research_analytics",
]

FORBIDDEN = ["order" + "_send", "execute" + "_order", "place" + "_order", "submit" + "_order"]


def scan_forbidden(path: Path) -> list:
    issues = []
    text = path.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        if bad in text:
            issues.append(f"{path.name}: contains '{bad}'")
    return issues


def main():
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    ok = True

    for mod in MODULES:
        try:
            importlib.import_module(mod)
            print(f"OK import {mod}")
        except Exception as e:
            print(f"FAIL import {mod}: {e}")
            ok = False

    for tool in TOOLS:
        p = PROJECT_ROOT / (tool.replace(".", "/") + ".py")
        if not p.exists():
            print(f"FAIL missing {p}")
            ok = False
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            print(f"OK py_compile {p.name}")
        except py_compile.PyCompileError as e:
            print(f"FAIL py_compile {p.name}: {e}")
            ok = False

    # Scan only Phase 17 new tools/modules for safety
    scan_dirs = [PROJECT_ROOT / "research_analytics", PROJECT_ROOT / "tools"]
    issues = []
    for d in scan_dirs:
        for f in d.glob("*.py"):
            issues.extend(scan_forbidden(f))
    if issues:
        for issue in issues:
            print(f"WARN {issue}")
    else:
        print("OK safety scan: no forbidden strings found.")

    if ok:
        print("OK all Phase 17 checks passed.")
        sys.exit(0)
    else:
        print("FAIL some Phase 17 checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
