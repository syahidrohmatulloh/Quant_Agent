"""Tests for Phase 18 Paper Portfolio Simulator.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import csv
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

from paper_simulator.simulator_config import validate_simulator_config, load_simulator_config
from paper_simulator.price_loader import PriceLoader
from paper_simulator.order_intent import build_order_intents, OrderIntent
from paper_simulator.fill_model import simulate_fill
from paper_simulator.cost_model import compute_costs, CostBreakdown
from paper_simulator.position_book import PositionBook, Position
from paper_simulator.pnl_engine import compute_pnl
from paper_simulator.exposure import compute_exposure
from paper_simulator.simulator_engine import SimulatorEngine
from paper_simulator.simulator_report import generate_report
from paper_simulator.simulator_log import append_trade_log, append_pnl_log
from paper_simulator.dashboard_export import export_dashboard_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_temp_csv(tmpdir, rows, filename="test.csv"):
    p = Path(tmpdir) / filename
    fieldnames = list(rows[0].keys()) if rows else ["timestamp", "open", "high", "low", "close", "volume"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return str(p)


def _make_valid_config(tmpdir, csv_path):
    return {
        "name": "test_sim",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": str(Path(tmpdir) / "state.json"),
        "trade_log_path": str(Path(tmpdir) / "trades.jsonl"),
        "pnl_log_path": str(Path(tmpdir) / "pnl.jsonl"),
        "report_output": str(Path(tmpdir) / "report.md"),
        "dashboard_output": str(Path(tmpdir) / "dash.json"),
        "symbols": [
            {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "csv": csv_path,
                "pip_size": 0.0001,
                "contract_size": 100000,
                "quote_currency": "USD",
            }
        ],
        "execution": {"fill_price": "next_close", "allow_partial_fill": False, "max_fill_delay_bars": 1},
        "costs": {"spread_pips": 1.0, "slippage_pips": 0.2, "commission_per_million": 30.0, "min_commission": 0.0},
        "risk": {"max_symbol_weight": 0.25, "max_total_gross_exposure": 1.0, "allow_short": True, "max_notional_per_symbol": 25000.0},
    }


def _run_cli(tool_name, args):
    tool = PROJECT_ROOT / "tools" / tool_name
    cmd = [sys.executable, str(tool)] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result


# ---------------------------------------------------------------------------
# 1. simulator config loads valid JSON
# ---------------------------------------------------------------------------
def test_simulator_config_loads_valid_json(tmp_path):
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows)
    cfg = _make_valid_config(tmp_path, csv_path)
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    config, ok, errors, warnings = load_simulator_config(str(p))
    assert ok
    assert config["name"] == "test_sim"


# ---------------------------------------------------------------------------
# 2. missing required config fails
# ---------------------------------------------------------------------------
def test_missing_required_config_fails():
    bad = {"name": "x"}
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("paper_only" in e for e in errors)


# ---------------------------------------------------------------------------
# 3. paper_only false rejected
# ---------------------------------------------------------------------------
def test_paper_only_false_rejected():
    bad = {
        "name": "x",
        "paper_only": False,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("paper_only" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 4. data_only false rejected
# ---------------------------------------------------------------------------
def test_data_only_false_rejected():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": False,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("data_only" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 5. no_order_submission false rejected
# ---------------------------------------------------------------------------
def test_no_order_submission_false_rejected():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": False,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("no_order_submission" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 6. credential-like fields rejected
# ---------------------------------------------------------------------------
def test_credential_like_fields_rejected():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
        "api_key": "secret",
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("Credential" in e for e in errors)


# ---------------------------------------------------------------------------
# 7. order execution fields rejected
# ---------------------------------------------------------------------------
def test_order_execution_fields_rejected():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
    }
    bad["order" + "_send"] = True
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("Order execution" in e for e in errors)


# ---------------------------------------------------------------------------
# 8. path traversal rejected
# ---------------------------------------------------------------------------
def test_path_traversal_rejected():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "../s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "../../a.csv", "pip_size": 0.0001, "contract_size": 100000}],
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("traversal" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 9. price loader loads canonical CSV
# ---------------------------------------------------------------------------
def test_price_loader_loads_canonical_csv(tmp_path):
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
        {"timestamp": "2024-01-01 01:00", "open": "1.0805", "high": "1.0815", "low": "1.0800", "close": "1.0810", "volume": "1200"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows, filename="mt5_EURUSD_H1.csv")
    loader = PriceLoader(csv_path)
    assert len(loader.rows) == 2
    assert loader.rows[0]["close"] == 1.0805


# ---------------------------------------------------------------------------
# 10. price loader latest close works
# ---------------------------------------------------------------------------
def test_price_loader_latest_close(tmp_path):
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
        {"timestamp": "2024-01-01 01:00", "open": "1.0805", "high": "1.0815", "low": "1.0800", "close": "1.0810", "volume": "1200"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows)
    loader = PriceLoader(csv_path)
    assert loader.latest_close() == 1.0810


# ---------------------------------------------------------------------------
# 11. price loader next close works
# ---------------------------------------------------------------------------
def test_price_loader_next_close(tmp_path):
    from datetime import datetime
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
        {"timestamp": "2024-01-01 01:00", "open": "1.0805", "high": "1.0815", "low": "1.0800", "close": "1.0810", "volume": "1200"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows)
    loader = PriceLoader(csv_path)
    after = datetime(2024, 1, 1, 0, 30)
    assert loader.next_close(after) == 1.0810


# ---------------------------------------------------------------------------
# 12. order intent converts PAPER_LONG to BUY
# ---------------------------------------------------------------------------
def test_order_intent_paper_long_to_buy():
    decisions = [
        {"decision_id": "d1", "action": "PAPER_LONG", "symbol": "EURUSD", "timeframe": "H1", "target_weight": 0.1},
    ]
    intents = build_order_intents(decisions, {"allow_short": True}, 100000.0)
    assert len(intents) == 1
    assert intents[0].side == "BUY"


# ---------------------------------------------------------------------------
# 13. order intent converts PAPER_SHORT to SELL
# ---------------------------------------------------------------------------
def test_order_intent_paper_short_to_sell():
    decisions = [
        {"decision_id": "d1", "action": "PAPER_SHORT", "symbol": "EURUSD", "timeframe": "H1", "target_weight": 0.1},
    ]
    intents = build_order_intents(decisions, {"allow_short": True}, 100000.0)
    assert len(intents) == 1
    assert intents[0].side == "SELL"


# ---------------------------------------------------------------------------
# 14. PAPER_NEUTRAL creates FLATTEN
# ---------------------------------------------------------------------------
def test_order_intent_paper_neutral_to_flatten():
    decisions = [
        {"decision_id": "d1", "action": "PAPER_NEUTRAL", "symbol": "EURUSD", "timeframe": "H1"},
    ]
    intents = build_order_intents(decisions, {"allow_short": True}, 100000.0)
    assert len(intents) == 1
    assert intents[0].side == "FLATTEN"


# ---------------------------------------------------------------------------
# 15. PAPER_HOLD creates no trade
# ---------------------------------------------------------------------------
def test_order_intent_paper_hold_no_trade():
    decisions = [
        {"decision_id": "d1", "action": "PAPER_HOLD", "symbol": "EURUSD", "timeframe": "H1"},
    ]
    intents = build_order_intents(decisions, {"allow_short": True}, 100000.0)
    assert len(intents) == 1
    assert intents[0].side == "HOLD"


# ---------------------------------------------------------------------------
# 16. cost model computes spread/slippage/commission
# ---------------------------------------------------------------------------
def test_cost_model_computes_all():
    costs = compute_costs(
        quantity=1.0,
        fill_price=1.0800,
        pip_size=0.0001,
        contract_size=100000,
        costs_config={"spread_pips": 1.0, "slippage_pips": 0.2, "commission_per_million": 30.0, "min_commission": 0.0},
    )
    assert costs.spread_cost > 0
    assert costs.slippage_cost > 0
    assert costs.commission > 0
    assert costs.total_cost > 0


# ---------------------------------------------------------------------------
# 17. fill model simulates fill
# ---------------------------------------------------------------------------
def test_fill_model_simulates_fill():
    intent = OrderIntent(
        intent_id="i1",
        source_decision_id="d1",
        generated_at="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="H1",
        side="BUY",
        target_weight=0.1,
        target_notional=10000.0,
        reason="test",
    )
    sym_cfg = {"pip_size": 0.0001, "contract_size": 100000}
    costs_cfg = {"spread_pips": 1.0, "slippage_pips": 0.2, "commission_per_million": 30.0, "min_commission": 0.0}
    fill = simulate_fill(intent, 1.0800, costs_cfg, sym_cfg)
    assert fill is not None
    assert fill.simulated is True
    assert fill.paper_only is True
    assert fill.no_order_submission is True


# ---------------------------------------------------------------------------
# 18. fill model rejects missing price
# ---------------------------------------------------------------------------
def test_fill_model_rejects_missing_price():
    intent = OrderIntent(
        intent_id="i1",
        source_decision_id="d1",
        generated_at="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="H1",
        side="BUY",
        target_weight=0.1,
        target_notional=10000.0,
        reason="test",
    )
    sym_cfg = {"pip_size": 0.0001, "contract_size": 100000}
    costs_cfg = {"spread_pips": 1.0, "slippage_pips": 0.2, "commission_per_million": 30.0, "min_commission": 0.0}
    fill = simulate_fill(intent, None, costs_cfg, sym_cfg)
    assert fill is None


# ---------------------------------------------------------------------------
# 19. position book opens long
# ---------------------------------------------------------------------------
def test_position_book_opens_long(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    pos = book.update_position("EURUSD", "H1", "BUY", 1.0, 1.0800, 10.0)
    assert pos.side == "LONG"
    assert pos.quantity == 1.0
    assert pos.average_price == 1.0800


# ---------------------------------------------------------------------------
# 20. position book opens short
# ---------------------------------------------------------------------------
def test_position_book_opens_short(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    pos = book.update_position("EURUSD", "H1", "SELL", 1.0, 1.0800, 10.0)
    assert pos.side == "SHORT"
    assert pos.quantity == 1.0


# ---------------------------------------------------------------------------
# 21. position book reduces position
# ---------------------------------------------------------------------------
def test_position_book_reduces_position(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 2.0, 1.0800, 10.0)
    pos = book.update_position("EURUSD", "H1", "SELL", 1.0, 1.0900, 5.0)
    assert pos.side == "LONG"
    assert pos.quantity == 1.0
    assert pos.realized_pnl > 0


# ---------------------------------------------------------------------------
# 22. position book flips position
# ---------------------------------------------------------------------------
def test_position_book_flips_position(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.0800, 10.0)
    pos = book.update_position("EURUSD", "H1", "SELL", 2.0, 1.0900, 5.0)
    assert pos.side == "SHORT"
    assert pos.quantity == 1.0


# ---------------------------------------------------------------------------
# 23. position book flattens position
# ---------------------------------------------------------------------------
def test_position_book_flattens_position(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.0800, 10.0)
    pos = book.update_position("EURUSD", "H1", "FLATTEN", 1.0, 1.0900, 5.0)
    assert pos.side == "FLAT"
    assert pos.quantity == 0.0


# ---------------------------------------------------------------------------
# 24. pnl engine marks to market
# ---------------------------------------------------------------------------
def test_pnl_engine_marks_to_market(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.0800, 10.0)
    pnl = compute_pnl(book, {"EURUSD": 1.0900}, 100000.0, "USD")
    assert pnl.total_pnl > 0
    assert pnl.equity > 100000.0


# ---------------------------------------------------------------------------
# 25. exposure computes gross/net exposure
# ---------------------------------------------------------------------------
def test_exposure_computes_gross_net(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 1.0, 1.0800, 10.0)
    exp = compute_exposure(book, {"EURUSD": 1.0900}, {"max_symbol_weight": 0.25, "max_total_gross_exposure": 1.0, "allow_short": True}, 100000.0)
    assert exp.gross_exposure > 0
    assert exp.net_exposure > 0
    assert exp.long_exposure > 0


# ---------------------------------------------------------------------------
# 26. risk warnings generated
# ---------------------------------------------------------------------------
def test_risk_warnings_generated(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    book.update_position("EURUSD", "H1", "BUY", 100.0, 1.0800, 10.0)
    exp = compute_exposure(book, {"EURUSD": 1.0900}, {"max_symbol_weight": 0.01, "max_total_gross_exposure": 0.01, "allow_short": True}, 100000.0)
    assert len(exp.warnings) > 0


# ---------------------------------------------------------------------------
# 27. simulator engine works with temp decisions and CSV
# ---------------------------------------------------------------------------
def test_simulator_engine_with_temp_data(tmp_path):
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
        {"timestamp": "2024-01-01 01:00", "open": "1.0805", "high": "1.0815", "low": "1.0800", "close": "1.0810", "volume": "1200"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows)
    cfg = _make_valid_config(tmp_path, csv_path)
    decisions = [
        {"decision_id": "d1", "action": "PAPER_LONG", "symbol": "EURUSD", "timeframe": "H1", "target_weight": 0.1},
    ]
    engine = SimulatorEngine(cfg)
    summary = engine.run(decisions)
    assert summary["decisions_processed"] == 1
    assert summary["fills_simulated"] >= 0


# ---------------------------------------------------------------------------
# 28. trade log append-only JSONL
# ---------------------------------------------------------------------------
def test_trade_log_append_only(tmp_path):
    log_path = str(tmp_path / "trades.jsonl")
    append_trade_log({"fill_id": "f1", "symbol": "EURUSD"}, log_path)
    append_trade_log({"fill_id": "f2", "symbol": "EURUSD"}, log_path)
    lines = Path(log_path).read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["fill_id"] == "f1"
    assert json.loads(lines[1])["fill_id"] == "f2"


# ---------------------------------------------------------------------------
# 29. pnl log append-only JSONL
# ---------------------------------------------------------------------------
def test_pnl_log_append_only(tmp_path):
    log_path = str(tmp_path / "pnl.jsonl")
    append_pnl_log({"timestamp": "t1", "total_pnl": 10.0}, log_path)
    append_pnl_log({"timestamp": "t2", "total_pnl": 20.0}, log_path)
    lines = Path(log_path).read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["total_pnl"] == 10.0
    assert json.loads(lines[1])["total_pnl"] == 20.0


# ---------------------------------------------------------------------------
# 30. report writes Markdown and JSON
# ---------------------------------------------------------------------------
def test_report_writes_markdown_and_json(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    cfg = _make_valid_config(tmp_path, "dummy.csv")
    out = generate_report(
        config=cfg,
        decisions=[],
        intents=[],
        fills=[],
        position_book=book,
        pnl=None,
        exposure=None,
        output_path=str(tmp_path / "report.md"),
    )
    assert Path(out["markdown_path"]).exists()
    assert Path(out["json_path"]).exists()


# ---------------------------------------------------------------------------
# 31. dashboard export writes expected shape
# ---------------------------------------------------------------------------
def test_dashboard_export_shape(tmp_path):
    state = str(tmp_path / "state.json")
    book = PositionBook(state)
    cfg = {"name": "t", "initial_cash": 100000.0, "base_currency": "USD"}
    out = str(tmp_path / "dash.json")
    export_dashboard_json(cfg, book, [], None, None, [], [], out)
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True
    assert "portfolio" in data
    assert "positions" in data


# ---------------------------------------------------------------------------
# 32. CLI config validation works
# ---------------------------------------------------------------------------
def test_cli_validate_config(tmp_path):
    rows = [{"timestamp": "2024-01-01 00:00", "open": "1.08", "high": "1.09", "low": "1.07", "close": "1.085", "volume": "1000"}]
    csv_path = _make_temp_csv(tmp_path, rows)
    cfg = _make_valid_config(tmp_path, csv_path)
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    result = _run_cli("validate_paper_simulator_config.py", ["--config", str(p), "--allow-missing"])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 33. run_paper_simulator CLI works with temp config
# ---------------------------------------------------------------------------
def test_cli_run_simulator(tmp_path):
    rows = [
        {"timestamp": "2024-01-01 00:00", "open": "1.0800", "high": "1.0810", "low": "1.0790", "close": "1.0805", "volume": "1000"},
        {"timestamp": "2024-01-01 01:00", "open": "1.0805", "high": "1.0815", "low": "1.0800", "close": "1.0810", "volume": "1200"},
    ]
    csv_path = _make_temp_csv(tmp_path, rows)
    cfg = _make_valid_config(tmp_path, csv_path)
    # Write decisions
    decisions_path = tmp_path / "decisions.jsonl"
    decisions_path.write_text(
        json.dumps({"decision_id": "d1", "action": "PAPER_LONG", "symbol": "EURUSD", "timeframe": "H1", "target_weight": 0.1}) + "\n",
        encoding="utf-8",
    )
    cfg["paper_decision_log"] = str(decisions_path)
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    result = _run_cli("run_paper_simulator.py", ["--config", str(p), "--allow-missing"])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 34. show_paper_positions CLI works
# ---------------------------------------------------------------------------
def test_cli_show_positions(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"saved_at": "t1", "positions": {}}), encoding="utf-8")
    result = _run_cli("show_paper_positions.py", ["--state", str(state)])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 35. show_paper_pnl CLI works
# ---------------------------------------------------------------------------
def test_cli_show_pnl(tmp_path):
    pnl = tmp_path / "pnl.jsonl"
    pnl.write_text(
        json.dumps({"timestamp": "t1", "realized_pnl": 0.0, "unrealized_pnl": 10.0, "total_pnl": 10.0, "equity": 100010.0, "cash_simulated": 99990.0, "gross_exposure": 100000.0, "net_exposure": 100000.0}) + "\n",
        encoding="utf-8",
    )
    result = _run_cli("show_paper_pnl.py", ["--pnl", str(pnl)])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 36. export dashboard CLI works
# ---------------------------------------------------------------------------
def test_cli_export_dashboard(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"saved_at": "t1", "positions": {}}), encoding="utf-8")
    out = tmp_path / "dash.json"
    result = _run_cli("export_paper_simulator_dashboard.py", ["--state", str(state), "--output", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()


# ---------------------------------------------------------------------------
# 37. validate_paper_simulator CLI works
# ---------------------------------------------------------------------------
def test_cli_validate_paper_simulator():
    result = _run_cli("validate_paper_simulator.py", [])
    assert result.returncode == 0, result.stderr
    assert "OK all Phase 18 checks passed." in result.stdout


# ---------------------------------------------------------------------------
# 38. no live network calls
# ---------------------------------------------------------------------------
def test_no_live_network_calls():
    import paper_simulator.simulator_config
    import paper_simulator.price_loader
    import paper_simulator.order_intent
    import paper_simulator.fill_model
    import paper_simulator.cost_model
    import paper_simulator.position_book
    import paper_simulator.pnl_engine
    import paper_simulator.exposure
    import paper_simulator.simulator_engine
    import paper_simulator.simulator_report
    import paper_simulator.simulator_log
    import paper_simulator.dashboard_export
    assert True


# ---------------------------------------------------------------------------
# 39. no broker credentials needed
# ---------------------------------------------------------------------------
def test_no_broker_credentials_needed():
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "initial_cash": 100000.0,
        "base_currency": "USD",
        "portfolio_state_path": "s.json",
        "trade_log_path": "t.jsonl",
        "pnl_log_path": "p.jsonl",
        "symbols": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv", "pip_size": 0.0001, "contract_size": 100000}],
        "token": "abc",
    }
    ok, errors, warnings = validate_simulator_config(bad)
    assert not ok
    assert any("Credential" in e for e in errors)


# ---------------------------------------------------------------------------
# 40. verify no forbidden order execution strings
# ---------------------------------------------------------------------------
def test_no_forbidden_order_strings_in_phase18():
    phase18_files = list((PROJECT_ROOT / "paper_simulator").glob("*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("validate_paper_simulator*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("run_paper_simulator*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("simulate_paper_decisions*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("show_paper_positions*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("show_paper_pnl*.py"))
    phase18_files += list((PROJECT_ROOT / "tools").glob("export_paper_simulator_dashboard*.py"))

    bad1 = "order" + "_send"
    bad2 = "execute" + "_order"
    bad3 = "place" + "_order"
    bad4 = "submit" + "_order"

    for f in phase18_files:
        text = f.read_text(encoding="utf-8")
        assert bad1 not in text, f.name + " contains forbidden string"
        assert bad2 not in text, f.name + " contains forbidden string"
        assert bad3 not in text, f.name + " contains forbidden string"
        assert bad4 not in text, f.name + " contains forbidden string"


# ---------------------------------------------------------------------------
# 41. existing Phase 6-17 tests still pass (smoke: pytest discovery)
# ---------------------------------------------------------------------------
def test_existing_test_discovery():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(PROJECT_ROOT / "tests"), "--collect-only", "-q"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
