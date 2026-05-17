"""
Test CLI tools import and run safely.
"""
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_list_strategies():
    result = subprocess.run(
        [sys.executable, "tools/list_strategies.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0
    assert "time_series_momentum" in result.stdout


def test_run_strategy_signal():
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_strategy_signal.py",
            "--strategy",
            "time_series_momentum",
            "--symbols",
            "EURUSD",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0
    assert "PAPER-ONLY" in result.stdout


def test_validate_strategy_library():
    result = subprocess.run(
        [sys.executable, "tools/validate_strategy_library.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0
    assert "overall_ok" in result.stdout
