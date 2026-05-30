"""Environment check for local app packaging.

Verifies Python version, project root structure, and key modules.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

_EXPECTED_MODULES = [
    "strategies",
    "strategy_lab",
    "market_data",
    "paper_orchestration",
    "data_manager",
    "research_analytics",
    "paper_simulator",
    "briefing",
]

_EXPECTED_TOOLS = [
    "run_dashboard_server.py",
    "run_daily_paper_workflow.py",
    "validate_briefing_config.py",
    "validate_paper_simulator_config.py",
    "validate_orchestration_config.py",
]


def check_environment(project_root: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    ok: List[str] = []

    # Python version
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 9):
        warnings.append(f"Python {py_version.major}.{py_version.minor} detected; recommend 3.9+")
    else:
        ok.append(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")

    # Project root looks like Quant_Agent
    if not project_root.exists():
        errors.append(f"Project root does not exist: {project_root}")
    else:
        ok.append(f"Project root exists: {project_root}")

    # Key modules
    for mod in _EXPECTED_MODULES:
        mod_path = project_root / mod
        init_path = mod_path / "__init__.py"
        if mod_path.exists() and init_path.exists():
            ok.append(f"Module found: {mod}")
        else:
            warnings.append(f"Missing optional module: {mod}")

    # Key tools
    tools_dir = project_root / "tools"
    for tool in _EXPECTED_TOOLS:
        tool_path = tools_dir / tool
        if tool_path.exists():
            ok.append(f"Tool found: {tool}")
        else:
            warnings.append(f"Missing optional tool: {tool}")

    # No required local data assumed
    ok.append("No required local data assumed (paper-only / data-only)")

    # No credentials required
    ok.append("No credentials required for local app packaging")

    return {
        "ok": ok,
        "warnings": warnings,
        "errors": errors,
        "healthy": len(errors) == 0,
    }
