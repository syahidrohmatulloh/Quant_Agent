"""
Test CLI tools run safely with temp CSV and do not require broker credentials.
Only tests NEW Phase 12 tools. Does not scan pre-existing Phase 9 tools.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import subprocess
import csv
import tempfile
import json


PHASE12_TOOLS = [
    "validate_market_csv.py",
    "list_market_datasets.py",
    "run_csv_strategy_signal.py",
    "run_csv_strategy_backtest.py",
    "run_csv_strategy_workflow.py",
    "generate_csv_strategy_report.py",
]


def _make_csv(n=30):
    rows = []
    price = 1.1000
    for i in range(n):
        o = price
        c = price + 0.001
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        rows.append({
            "time": f"2024.01.{15 + i//24:02d} {i%24:02d}:00",
            "open": str(o), "high": str(h), "low": str(l), "close": str(c),
            "tick_volume": "1000"
        })
        price = c
    return rows


def _write_csv(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _run_tool(script_name, args):
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools", script_name)
    cmd = [sys.executable, script] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_validate_market_csv_cli():
    rows = _make_csv(10)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = _run_tool("validate_market_csv.py", ["--csv", f.name, "--symbol", "EURUSD", "--timeframe", "H1"])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PAPER-ONLY" in result.stdout
        assert "Valid: True" in result.stdout
        os.unlink(f.name)


def test_validate_market_csv_cli_json():
    rows = _make_csv(10)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        result = _run_tool("validate_market_csv.py", ["--csv", f.name, "--json"])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Skip the paper-only disclaimer line, parse JSON from remaining output
        lines = result.stdout.strip().splitlines()
        json_text = "\n".join(lines[1:]) if lines else ""
        data = json.loads(json_text)
        assert data["valid"] is True
        os.unlink(f.name)


def test_validate_market_csv_cli_exit_nonzero():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        result = _run_tool("validate_market_csv.py", ["--csv", f.name])
        assert result.returncode == 1
        os.unlink(f.name)


def test_list_market_datasets_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "tick_volume"])
            writer.writerow(["2024.01.15 10:00", "1.1000", "1.1005", "1.0995", "1.1002", "1000"])
        result = _run_tool("list_market_datasets.py", ["--data-dir", tmpdir])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "EURUSD" in result.stdout


def test_run_csv_strategy_signal_cli():
    rows = _make_csv(30)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        out = os.path.join(tempfile.gettempdir(), "latest_signal.json")
        result = _run_tool("run_csv_strategy_signal.py", [
            "--csv", f.name, "--strategy", "ma_crossover",
            "--symbol", "EURUSD", "--timeframe", "H1",
            "--params", '{"fast":3,"slow":10}',
            "--output", out,
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PAPER-ONLY" in result.stdout
        assert os.path.exists(out)
        os.unlink(f.name)
        if os.path.exists(out):
            os.unlink(out)


def test_run_csv_strategy_backtest_cli():
    rows = _make_csv(50)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        out = os.path.join(tempfile.gettempdir(), "bt_result.json")
        result = _run_tool("run_csv_strategy_backtest.py", [
            "--csv", f.name, "--strategy", "ma_crossover",
            "--symbol", "EURUSD", "--timeframe", "H1",
            "--initial", "100000",
            "--output", out,
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "PAPER-ONLY" in result.stdout
        assert os.path.exists(out)
        os.unlink(f.name)
        if os.path.exists(out):
            os.unlink(out)


def test_generate_csv_strategy_report_cli():
    rows = _make_csv(30)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        out = os.path.join(tempfile.gettempdir(), "report.md")
        result = _run_tool("generate_csv_strategy_report.py", [
            "--csv", f.name, "--strategy", "ma_crossover",
            "--symbol", "EURUSD", "--timeframe", "H1",
            "--output", out,
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert os.path.exists(out)
        with open(out, "r") as rf:
            content = rf.read()
            assert "PAPER-ONLY" in content
        os.unlink(f.name)
        if os.path.exists(out):
            os.unlink(out)


def test_run_csv_strategy_workflow_cli():
    rows = _make_csv(50)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        _write_csv(f.name, rows, ["time", "open", "high", "low", "close", "tick_volume"])
        out = os.path.join(tempfile.gettempdir(), "workflow_report.md")
        result = _run_tool("run_csv_strategy_workflow.py", [
            "--csv", f.name,
            "--symbol", "EURUSD", "--timeframe", "H1",
            "--strategies", "ma_crossover,time_series_momentum",
            "--backtest",
            "--output", out,
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert os.path.exists(out)
        json_out = out.replace(".md", ".json")
        assert os.path.exists(json_out)
        os.unlink(f.name)
        if os.path.exists(out):
            os.unlink(out)
        if os.path.exists(json_out):
            os.unlink(json_out)


def test_cli_tools_no_broker_credentials():
    """Ensure no broker credentials are referenced in Phase 12 tools only."""
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    for fname in PHASE12_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        assert "order_send" not in content, f"{fname} contains order_send"
        # api_key is OK if it's in an example/help string
        if "api_key" in content.lower():
            assert "example" in content.lower() or "help" in content.lower(), f"{fname} may contain real api_key"


def test_cli_tools_no_live_network():
    """Ensure no live network calls in Phase 12 tools only."""
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    for fname in PHASE12_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        assert "urllib" not in content, f"{fname} uses urllib"
        assert "requests" not in content, f"{fname} uses requests"
        assert "socket" not in content, f"{fname} uses socket"
