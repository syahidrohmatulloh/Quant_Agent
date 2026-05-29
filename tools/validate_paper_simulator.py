"""Validate all Phase 18 modules and tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import py_compile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
    print("Validating Phase 18 modules and tools...")

    modules = [
        "paper_simulator/__init__.py",
        "paper_simulator/simulator_config.py",
        "paper_simulator/price_loader.py",
        "paper_simulator/order_intent.py",
        "paper_simulator/fill_model.py",
        "paper_simulator/cost_model.py",
        "paper_simulator/position_book.py",
        "paper_simulator/pnl_engine.py",
        "paper_simulator/exposure.py",
        "paper_simulator/simulator_engine.py",
        "paper_simulator/simulator_report.py",
        "paper_simulator/simulator_log.py",
        "paper_simulator/dashboard_export.py",
    ]

    tools = [
        "tools/validate_paper_simulator_config.py",
        "tools/run_paper_simulator.py",
        "tools/simulate_paper_decisions.py",
        "tools/show_paper_positions.py",
        "tools/show_paper_pnl.py",
        "tools/export_paper_simulator_dashboard.py",
        "tools/validate_paper_simulator.py",
    ]

    all_ok = True
    for rel in modules + tools:
        p = PROJECT_ROOT / rel
        if not p.exists():
            print("  MISSING: " + rel)
            all_ok = False
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            print("  OK:      " + rel)
        except py_compile.PyCompileError as e:
            print("  FAIL:    " + rel + " -> " + str(e))
            all_ok = False

    # Safety scan: check for forbidden strings in Phase 18 files only
    bad1 = "order" + "_send"
    bad2 = "execute" + "_order"
    bad3 = "place" + "_order"
    bad4 = "submit" + "_order"

    phase18_files = list((PROJECT_ROOT / "paper_simulator").glob("*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("validate_paper_simulator*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("run_paper_simulator*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("simulate_paper_decisions*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("show_paper_positions*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("show_paper_pnl*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("export_paper_simulator_dashboard*.py"))

    safety_ok = True
    for f in phase18_files:
        text = f.read_text(encoding="utf-8")
        if bad1 in text:
            print("  SAFETY FAIL: " + f.name + " contains forbidden string")
            safety_ok = False
        if bad2 in text:
            print("  SAFETY FAIL: " + f.name + " contains forbidden string")
            safety_ok = False
        if bad3 in text:
            print("  SAFETY FAIL: " + f.name + " contains forbidden string")
            safety_ok = False
        if bad4 in text:
            print("  SAFETY FAIL: " + f.name + " contains forbidden string")
            safety_ok = False

    if all_ok and safety_ok:
        print("OK all Phase 18 checks passed.")
        sys.exit(0)
    else:
        print("Some Phase 18 checks FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
