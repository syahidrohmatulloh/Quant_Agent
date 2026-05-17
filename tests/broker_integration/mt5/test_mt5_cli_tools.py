"""Test MT5 CLI tools safely without a real MT5 terminal."""
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


FAKE_MT5_MODULE = r'''
class FakeSymbol:
    def __init__(self, name):
        self.name = name

class FakeTick:
    time = 1700000000
    bid = 1.1001
    ask = 1.1003
    last = 1.1002
    volume = 100
    time_msc = 1700000000123
    flags = 1


def initialize(timeout=60000, portable=False):
    return True


def last_error():
    return (0, "OK")


def symbols_get():
    return [FakeSymbol("EURUSD")]


def symbol_info_tick(symbol):
    return FakeTick()


def copy_rates_from_pos(symbol, timeframe, start_pos, count):
    return [
        (1700000000, 1.1000, 1.1005, 1.0995, 1.1002, 1000, 2, 5000),
        (1700003600, 1.1002, 1.1008, 1.1000, 1.1005, 1200, 2, 6000),
    ]


def copy_rates_range(symbol, timeframe, date_from, date_to):
    return [
        (1700000000, 1.1000, 1.1005, 1.0995, 1.1002, 1000, 2, 5000),
    ]


def shutdown():
    return None
'''


def _env_without_project_root():
    env = dict(os.environ)
    paths = env.get("PYTHONPATH", "").split(os.pathsep) if env.get("PYTHONPATH") else []
    paths = [p for p in paths if Path(p).resolve() != PROJECT_ROOT.resolve()]
    if paths:
        env["PYTHONPATH"] = os.pathsep.join(paths)
    else:
        env.pop("PYTHONPATH", None)
    return env


def _env_with_fake_mt5(tmp_path):
    fake_dir = tmp_path / "fake_mt5"
    fake_dir.mkdir()
    (fake_dir / "MetaTrader5.py").write_text(FAKE_MT5_MODULE, encoding="utf-8")
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(fake_dir) if not existing else str(fake_dir) + os.pathsep + existing
    return env


def test_diagnose_mt5_module_missing():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools/diagnose_mt5_connection.py")],
        capture_output=True,
        text=True,
        cwd="/tmp",
        env=_env_without_project_root(),
    )
    assert result.returncode == 1
    assert "NOT installed" in result.stdout or "NOT installed" in result.stderr


def test_diagnose_mt5_success_with_fake_module(tmp_path):
    result = subprocess.run(
        [sys.executable, "tools/diagnose_mt5_connection.py"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=_env_with_fake_mt5(tmp_path),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "PAPER-ONLY" in result.stdout
    assert "MT5 terminal initialized" in result.stdout


def test_fetch_mt5_snapshot_success_with_fake_module(tmp_path):
    result = subprocess.run(
        [sys.executable, "tools/fetch_mt5_snapshot.py", "--symbol", "EURUSD"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=_env_with_fake_mt5(tmp_path),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "PAPER-ONLY" in result.stdout
    assert "bid" in result.stdout


def test_run_mt5_strategy_signal_success_with_fake_module(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_mt5_strategy_signal.py",
            "--strategy",
            "time_series_momentum",
            "--symbol",
            "EURUSD",
            "--timeframe",
            "H1",
            "--count",
            "2",
            "--params",
            '{"lookback": 1, "threshold": 0.0001}',
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=_env_with_fake_mt5(tmp_path),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "PAPER-ONLY" in result.stdout
    assert "signals" in result.stdout
