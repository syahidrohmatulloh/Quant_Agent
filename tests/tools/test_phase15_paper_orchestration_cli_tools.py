"""
Tests for Phase 15 CLI tools.
Paper-only. No live trading. No broker credentials. No network.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PYTHON = sys.executable


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def valid_orchestration_config(temp_dir):
    exp_cfg = {
        "name": "test_exp",
        "paper_only": True,
        "data_only": True,
        "symbols": [
            {"symbol": "EURUSD", "timeframe": "H1", "csv": str(temp_dir / "eurusd.csv")}
        ],
        "strategies": [
            {"name": "ma_crossover", "params": {"fast": 5, "slow": 20}}
        ],
        "backtest": False,
        "consensus": {"method": "majority_vote", "minimum_agreement": 0.6},
    }
    exp_path = temp_dir / "experiment.json"
    with open(exp_path, "w") as f:
        json.dump(exp_cfg, f)

    orch_cfg = {
        "name": "test_workflow",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "experiment_config": str(exp_path),
        "portfolio_state_path": str(temp_dir / "state.json"),
        "decision_log_path": str(temp_dir / "decisions.jsonl"),
        "audit_log_path": str(temp_dir / "audit.jsonl"),
        "dashboard_output_path": str(temp_dir / "dash.json"),
        "daily_report_output": str(temp_dir / "report.md"),
        "risk": {
            "max_symbol_weight": 0.25,
            "max_total_gross_exposure": 1.0,
            "max_new_decisions_per_run": 10,
            "allow_short": True,
            "conflict_action": "neutral",
        },
        "decision_policy": {
            "minimum_consensus_confidence": "medium",
            "allow_low_confidence": False,
            "neutral_on_conflict": True,
        },
    }
    orch_path = temp_dir / "orchestration.json"
    with open(orch_path, "w") as f:
        json.dump(orch_cfg, f)
    return str(orch_path), str(temp_dir)


def _run_tool(script_name, args, cwd=PROJECT_ROOT):
    cmd = [PYTHON, str(PROJECT_ROOT / "tools" / script_name)] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=env)
    return result


def test_validate_orchestration_config_cli_help():
    result = _run_tool("validate_orchestration_config.py", ["--help"])
    assert result.returncode == 0
    assert "Validate paper orchestration config" in result.stdout


def test_validate_orchestration_config_cli_runs(valid_orchestration_config):
    orch_path, _ = valid_orchestration_config
    result = _run_tool("validate_orchestration_config.py", ["--config", orch_path, "--allow-missing"])
    assert result.returncode == 0, result.stderr
    assert "VALID" in result.stdout


def test_show_paper_portfolio_cli_help():
    result = _run_tool("show_paper_portfolio.py", ["--help"])
    assert result.returncode == 0


def test_show_paper_portfolio_cli_runs(temp_dir):
    state_path = temp_dir / "state.json"
    from paper_orchestration.paper_portfolio import PaperPortfolio
    PaperPortfolio(str(state_path))
    result = _run_tool("show_paper_portfolio.py", ["--state", str(state_path)])
    assert result.returncode == 0, result.stderr
    assert "paper_only" in result.stdout


def test_reset_paper_portfolio_cli_refuses_without_confirm(temp_dir):
    state_path = temp_dir / "state.json"
    from paper_orchestration.paper_portfolio import PaperPortfolio
    PaperPortfolio(str(state_path))
    result = _run_tool("reset_paper_portfolio.py", ["--state", str(state_path)])
    assert result.returncode != 0


def test_reset_paper_portfolio_cli_confirms(temp_dir):
    state_path = temp_dir / "state.json"
    from paper_orchestration.paper_portfolio import PaperPortfolio
    pf = PaperPortfolio(str(state_path))
    pf.update_positions([{"action": "PAPER_LONG", "symbol": "X", "timeframe": "H1", "target_weight": 0.1, "confidence_label": "medium", "generated_at": "2026-01-01T00:00:00+00:00"}], "r1")
    result = _run_tool("reset_paper_portfolio.py", ["--state", str(state_path), "--confirm-reset"])
    assert result.returncode == 0, result.stderr
    assert "reset" in result.stdout.lower() or "Portfolio state reset" in result.stdout


def test_generate_scheduler_command_cli_help():
    result = _run_tool("generate_scheduler_command.py", ["--help"])
    assert result.returncode == 0


def test_generate_scheduler_command_cli_runs(valid_orchestration_config):
    orch_path, _ = valid_orchestration_config
    result = _run_tool("generate_scheduler_command.py", ["--config", orch_path, "--project-root", str(PROJECT_ROOT)])
    assert result.returncode == 0, result.stderr
    assert "run_daily_paper_workflow.py" in result.stdout
    assert "Disclaimer" in result.stdout


def test_validate_paper_orchestration_cli():
    result = _run_tool("validate_paper_orchestration.py", [])
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_run_daily_paper_workflow_cli_help():
    result = _run_tool("run_daily_paper_workflow.py", ["--help"])
    assert result.returncode == 0


def test_run_daily_paper_workflow_cli_with_temp_csv(temp_dir):
    """End-to-end: create temp CSV, temp experiment config, temp orchestration config, run workflow."""
    csv_path = temp_dir / "eurusd.csv"
    header = "timestamp,open,high,low,close,volume\n"
    rows = []
    for i in range(30):
        rows.append(f"2026-01-{i+1:02d}T00:00:00,{1.0+i*0.001},{1.001+i*0.001},{0.999+i*0.001},{1.0005+i*0.001},1000\n")
    csv_path.write_text(header + "".join(rows))

    exp_cfg = {
        "name": "test_exp",
        "paper_only": True,
        "data_only": True,
        "symbols": [
            {"symbol": "EURUSD", "timeframe": "H1", "csv": str(csv_path)}
        ],
        "strategies": [
            {"name": "ma_crossover", "params": {"fast": 5, "slow": 20}}
        ],
        "backtest": False,
        "consensus": {"method": "majority_vote", "minimum_agreement": 0.6},
    }
    exp_path = temp_dir / "experiment.json"
    with open(exp_path, "w") as f:
        json.dump(exp_cfg, f)

    orch_cfg = {
        "name": "test_workflow",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "experiment_config": str(exp_path),
        "portfolio_state_path": str(temp_dir / "state.json"),
        "decision_log_path": str(temp_dir / "decisions.jsonl"),
        "audit_log_path": str(temp_dir / "audit.jsonl"),
        "dashboard_output_path": str(temp_dir / "dash.json"),
        "daily_report_output": str(temp_dir / "report.md"),
        "risk": {
            "max_symbol_weight": 0.25,
            "max_total_gross_exposure": 1.0,
            "max_new_decisions_per_run": 10,
            "allow_short": True,
            "conflict_action": "neutral",
        },
        "decision_policy": {
            "minimum_consensus_confidence": "medium",
            "allow_low_confidence": False,
            "neutral_on_conflict": True,
        },
    }
    orch_path = temp_dir / "orchestration.json"
    with open(orch_path, "w") as f:
        json.dump(orch_cfg, f)

    result = _run_tool("run_daily_paper_workflow.py", ["--config", str(orch_path)])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    assert "Workflow completed successfully" in result.stdout
    assert (temp_dir / "state.json").exists()
    assert (temp_dir / "decisions.jsonl").exists()
    assert (temp_dir / "audit.jsonl").exists()
    assert (temp_dir / "dash.json").exists()
    assert (temp_dir / "report.md").exists()
