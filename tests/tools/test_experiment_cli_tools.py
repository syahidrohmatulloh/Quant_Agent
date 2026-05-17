"""
Test Phase 13 CLI tools run safely with temp config and do not require broker credentials.
Only tests NEW Phase 13 tools. Does not scan pre-existing tools.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import subprocess
import csv
import tempfile
import json

PHASE13_TOOLS = [
    "validate_experiment_config.py",
    "run_strategy_experiment.py",
    "compare_strategy_signals.py",
    "generate_daily_decision_report.py",
    "export_experiment_dashboard.py",
    "list_experiment_history.py",
]


def _make_csv(n=50):
    rows = []
    price = 1.1000
    for i in range(n):
        o = price
        c = price + 0.001
        h = max(o, c) + 0.0005
        l = min(o, c) - 0.0005
        rows.append({
            "time": "2024.01." + str(15 + i//24).zfill(2) + " " + str(i%24).zfill(2) + ":00",
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


def _make_config(tmpdir, csv_path):
    config = {
        "name": "test_experiment",
        "paper_only": True,
        "data_only": True,
        "symbols": [
            {"symbol": "EURUSD", "timeframe": "H1", "csv": csv_path}
        ],
        "strategies": [
            {"name": "ma_crossover", "params": {"fast": 3, "slow": 10}}
        ],
        "backtest": False,
        "consensus": {"method": "majority_vote", "minimum_agreement": 0.6},
    }
    config_path = os.path.join(tmpdir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config_path


def _run_tool(script_name, args):
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools", script_name)
    cmd = [sys.executable, script] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_validate_experiment_config_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, _make_csv(30), ["time", "open", "high", "low", "close", "tick_volume"])
        config_path = _make_config(tmpdir, csv_path)
        result = _run_tool("validate_experiment_config.py", ["--config", config_path])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "Valid: True" in result.stdout


def test_validate_experiment_config_cli_rejects_bad():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "name": "bad",
            "paper_only": False,
            "data_only": True,
            "symbols": [],
            "strategies": [],
        }
        config_path = os.path.join(tmpdir, "bad.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
        result = _run_tool("validate_experiment_config.py", ["--config", config_path])
        assert result.returncode == 1
        assert "paper_only must be true" in result.stdout


def test_run_strategy_experiment_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, _make_csv(50), ["time", "open", "high", "low", "close", "tick_volume"])
        config_path = _make_config(tmpdir, csv_path)
        out_dir = os.path.join(tmpdir, "reports")
        dash_dir = os.path.join(tmpdir, "dashboard")
        hist_dir = os.path.join(tmpdir, "history")
        result = _run_tool("run_strategy_experiment.py", [
            "--config", config_path,
            "--output-dir", out_dir,
            "--dashboard-dir", dash_dir,
            "--history-dir", hist_dir,
        ])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "Experiment complete" in result.stdout


def test_compare_strategy_signals_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, _make_csv(50), ["time", "open", "high", "low", "close", "tick_volume"])
        config_path = _make_config(tmpdir, csv_path)
        result = _run_tool("compare_strategy_signals.py", [
            "--config", config_path, "--symbol", "EURUSD"
        ])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert "PAPER-ONLY" in result.stdout
        assert "Consensus:" in result.stdout


def test_generate_daily_decision_report_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, _make_csv(50), ["time", "open", "high", "low", "close", "tick_volume"])
        config_path = _make_config(tmpdir, csv_path)
        out_path = os.path.join(tmpdir, "daily.md")
        result = _run_tool("generate_daily_decision_report.py", [
            "--config", config_path, "--output", out_path,
        ])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert os.path.exists(out_path)
        with open(out_path, "r") as f:
            content = f.read()
        assert "PAPER-ONLY" in content


def test_export_experiment_dashboard_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mt5_EURUSD_H1.csv")
        _write_csv(csv_path, _make_csv(50), ["time", "open", "high", "low", "close", "tick_volume"])
        config_path = _make_config(tmpdir, csv_path)
        out_path = os.path.join(tmpdir, "dash.json")
        result = _run_tool("export_experiment_dashboard.py", [
            "--config", config_path, "--output", out_path,
        ])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert os.path.exists(out_path)
        with open(out_path, "r") as f:
            data = json.load(f)
        assert data["paper_only"] is True
        assert "summary" in data


def test_list_experiment_history_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        from experiment_manager.experiment_log import append_experiment_log
        append_experiment_log(tmpdir, "run001", "exp1", "cfg.json", 2, 3, "res.json", "dash.json")
        result = _run_tool("list_experiment_history.py", ["--history-dir", tmpdir])
        assert result.returncode == 0, "stderr: " + result.stderr
        assert "run001" in result.stdout
        assert "exp1" in result.stdout


def test_cli_tools_have_help():
    for tool in PHASE13_TOOLS:
        result = _run_tool(tool, ["--help"])
        assert result.returncode == 0, tool + " --help failed: " + result.stderr


def test_cli_tools_no_broker_credentials():
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    for fname in PHASE13_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        assert "order_send" not in content, fname + " contains order_send"


def test_cli_tools_no_live_network():
    tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools")
    for fname in PHASE13_TOOLS:
        with open(os.path.join(tools_dir, fname), "r", encoding="utf-8") as f:
            content = f.read()
        assert "urllib" not in content, fname + " uses urllib"
        assert "requests" not in content, fname + " uses requests"
        assert "socket" not in content, fname + " uses socket"
