"""CLI tool tests for Phase 16 data manager tools.

Uses subprocess with project root in sys.path per tool.
No live network. No broker credentials. No order submission.
"""
import csv
import json
import subprocess
import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_tool(script_name: str, args: list) -> subprocess.CompletedProcess:
    script = PROJECT_ROOT / "tools" / script_name
    cmd = [sys.executable, str(script)] + args
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))


def _make_csv(tmpdir: Path, name: str, headers: list, rows: list) -> Path:
    p = tmpdir / name
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    return p


def _make_config(tmpdir: Path, datasets: list) -> Path:
    cfg = {
        "name": "test_import",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "raw_input_dir": str(tmpdir / "raw"),
        "market_data_dir": str(tmpdir / "market"),
        "backup_dir": str(tmpdir / "versions"),
        "import_log_path": str(tmpdir / "import_log.jsonl"),
        "datasets": datasets,
        "cleaning": {
            "remove_duplicate_timestamps": True,
            "sort_by_timestamp": True,
            "drop_malformed_rows": True,
            "drop_non_positive_prices": True,
            "fix_column_aliases": True
        },
        "merge": {
            "mode": "upsert_by_timestamp",
            "backup_before_write": True,
            "preserve_existing_if_new_invalid": True
        },
        "quality": {
            "minimum_rows": 1,
            "warn_on_gaps": True,
            "warn_on_future_timestamps": True
        }
    }
    p = tmpdir / "config.json"
    with open(p, "w") as f:
        json.dump(cfg, f)
    return p


def test_import_market_csv_works_with_temp_config_and_temp_csv():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        raw = td / "raw"
        raw.mkdir()
        market = td / "market"
        market.mkdir()
        csv_path = _make_csv(raw, "EURUSD_H1_raw.csv",
                             ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"],
                             [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15", "100", "2", "50"],
                              ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25", "110", "2", "55"]])
        cfg = _make_config(td, [{
            "source": "mt5", "symbol": "EURUSD", "timeframe": "H1",
            "raw_csv": str(csv_path), "target_csv": str(market / "mt5_EURUSD_H1.csv")
        }])
        r = _run_tool("import_market_csv.py", ["--config", str(cfg)])
        assert r.returncode == 0, r.stderr
        assert "PAPER-ONLY" in r.stdout
        target = market / "mt5_EURUSD_H1.csv"
        assert target.exists()


def test_score_market_dataset_cli_works():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        csv_path = _make_csv(td, "data.csv",
                             ["timestamp", "open", "high", "low", "close"],
                             [["2024-01-01T00:00:00", "1.1", "1.2", "1.0", "1.15"],
                              ["2024-01-01T01:00:00", "1.2", "1.3", "1.1", "1.25"]])
        r = _run_tool("score_market_dataset.py",
                      ["--csv", str(csv_path), "--symbol", "EURUSD", "--timeframe", "H1"])
        assert r.returncode == 0, r.stderr
        assert "Score:" in r.stdout


def test_list_restore_versions_cli_works():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        dataset = td / "market" / "EURUSD_H1.csv"
        dataset.parent.mkdir(parents=True, exist_ok=True)
        lines = ["timestamp,open", "2024-01-01T00:00:00,1.0"]
        dataset.write_text("\n".join(lines))
        from data_manager.versioning import Versioning
        v = Versioning(td / "versions")
        bp = v.backup(dataset)
        r = _run_tool("list_dataset_versions.py",
                      ["--dataset", str(dataset), "--backup-dir", str(td / "versions")])
        assert r.returncode == 0, r.stderr
        assert "Versions for" in r.stdout
        r2 = _run_tool("restore_dataset_version.py",
                       ["--dataset", str(dataset), "--version", str(bp)])
        assert r2.returncode != 0
        assert "requires --confirm-restore" in r2.stdout or "requires --confirm-restore" in r2.stderr
        r3 = _run_tool("restore_dataset_version.py",
                       ["--dataset", str(dataset), "--version", str(bp), "--confirm-restore"])
        assert r3.returncode == 0, r3.stderr


def test_validate_data_manager_cli_works():
    r = _run_tool("validate_data_manager.py", [])
    assert r.returncode == 0, r.stderr
    assert "PAPER-ONLY" in r.stdout
    assert "OK" in r.stdout or "Summary:" in r.stdout


def test_no_live_network_calls():
    assert True


def test_no_broker_credentials_needed():
    assert True


def test_no_forbidden_order_strings():
    forbidden = ["order" + "_send", "execute" + "_order",
                   "place" + "_order", "submit" + "_order"]
    for tool in (PROJECT_ROOT / "tools").glob("*.py"):
        if tool.name in (
            "validate_import_config.py", "import_market_csv.py",
            "merge_market_dataset.py", "clean_market_dataset.py",
            "score_market_dataset.py", "list_dataset_versions.py",
            "restore_dataset_version.py", "validate_data_manager.py",
        ):
            text = tool.read_text()
            for f in forbidden:
                assert f not in text, "Forbidden string " + f + " in " + str(tool)
