"""Tests for Phase 22 documentation CLI tools.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run_tool(tool_name, extra_args=None, cwd=None):
    cmd = [sys.executable, f"tools/{tool_name}"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result


def test_validate_docs_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text(
            "# Project\n\nPaper-only. Data-only. No live trading. "
            "No order submission. Not financial advice. Does not guarantee performance.\n\n"
            "[Architecture](docs/ARCHITECTURE.md)\n"
            "[Setup](docs/SETUP.md)\n"
            "[Safety](docs/SAFETY_AND_LIMITATIONS.md)\n"
            "[Troubleshooting](docs/TROUBLESHOOTING.md)\n"
        )
        (root / "docs").mkdir(parents=True, exist_ok=True)
        for doc in ["ARCHITECTURE.md", "SETUP.md", "COMMAND_CHEATSHEET.md",
                    "DAILY_WORKFLOW.md", "DASHBOARD_GUIDE.md", "SAFETY_AND_LIMITATIONS.md",
                    "TROUBLESHOOTING.md", "PHASE_HISTORY.md", "DEMO_SCRIPT.md", "POST_MVP_ROADMAP.md"]:
            (root / "docs" / doc).write_text("# Doc\n\nPaper-only. No live trading.")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        src_docs_tools = Path(__file__).resolve().parents[2] / "docs_tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)
        if src_docs_tools.exists():
            shutil.copytree(src_docs_tools, root / "docs_tools", dirs_exist_ok=True)

        result = _run_tool("validate_docs.py", cwd=root)
        assert result.returncode == 0
        assert "Docs validation OK" in result.stdout or "PASSED" in result.stdout


def test_show_demo_script_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "DEMO_SCRIPT.md").write_text("# Demo\n\nStep 1: Run tests.")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)

        result = _run_tool("show_demo_script.py", cwd=root)
        assert result.returncode == 0
        assert "Demo" in result.stdout or "Step 1" in result.stdout


def test_show_demo_script_summary_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "DEMO_SCRIPT.md").write_text("# Demo\n\n## Intro\n\n## Tests\n\n## Dashboard")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)

        result = _run_tool("show_demo_script.py", ["--summary"], cwd=root)
        assert result.returncode == 0
        assert "Demo Script Summary" in result.stdout or "Intro" in result.stdout


def test_show_command_cheatsheet_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "COMMAND_CHEATSHEET.md").write_text("# Commands\n\npytest\n")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)

        result = _run_tool("show_command_cheatsheet.py", cwd=root)
        assert result.returncode == 0
        assert "Commands" in result.stdout or "pytest" in result.stdout


def test_show_command_cheatsheet_summary_cli_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "COMMAND_CHEATSHEET.md").write_text("# Commands\n\npytest\n")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)

        result = _run_tool("show_command_cheatsheet.py", ["--summary"], cwd=root)
        assert result.returncode == 0
        assert "Command Categories" in result.stdout or "test" in result.stdout


def test_validate_docs_cli_fails_on_missing_docs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Project\n")

        import shutil
        src_tools = Path(__file__).resolve().parents[2] / "tools"
        if src_tools.exists():
            shutil.copytree(src_tools, root / "tools", dirs_exist_ok=True)
        src_docs_tools = Path(__file__).resolve().parents[2] / "docs_tools"
        if src_docs_tools.exists():
            shutil.copytree(src_docs_tools, root / "docs_tools", dirs_exist_ok=True)

        result = _run_tool("validate_docs.py", cwd=root)
        assert result.returncode == 1
        assert "FAIL" in result.stdout or "FAILED" in result.stdout
