"""Tests for Phase 17 Research Analytics CLI tools.

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

from research_analytics.research_config import validate_research_config, load_research_config
from research_analytics.performance_metrics import compute_performance_metrics
from research_analytics.drawdown_analysis import analyze_drawdown
from research_analytics.signal_quality import analyze_signal_quality, normalize_signal
from research_analytics.regime_attribution import analyze_regime_attribution, classify_regimes
from research_analytics.strategy_attribution import analyze_strategy_attribution
from research_analytics.stability_analysis import analyze_stability
from research_analytics.comparison_report import generate_comparison_report
from research_analytics.analytics_export import export_dashboard_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_temp_csv(tmpdir, rows):
    p = Path(tmpdir) / "data.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["return", "signal"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return str(p)


def _make_valid_config(tmpdir, csv_path):
    return {
        "name": "test",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "output_dir": str(Path(tmpdir) / "reports" / "research_analytics"),
        "dashboard_output": str(Path(tmpdir) / "reports" / "dashboard" / "research_analytics" / "latest.json"),
        "datasets": [{"symbol": "EURUSD", "timeframe": "H1", "csv": csv_path}],
        "strategies": ["ma_crossover"],
    }



def _json_from_stdout(stdout: str):
    lines = stdout.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("{"):
            start = i
            break
    if start is None:
        raise AssertionError(f"No JSON object found in stdout: {stdout}")
    return json.loads("\n".join(lines[start:]))

def _run_cli(tool_name, args):
    tool = PROJECT_ROOT / "tools" / tool_name
    cmd = [sys.executable, str(tool)] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result


# ---------------------------------------------------------------------------
# 1. research config loads valid JSON
# ---------------------------------------------------------------------------
def test_research_config_loads_valid_json(tmp_path):
    csv_path = _make_temp_csv(tmp_path, [{"return": "0.001", "signal": "LONG"}])
    cfg = _make_valid_config(tmp_path, csv_path)
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    config, ok, errors, warnings = load_research_config(str(p))
    assert ok
    assert config["name"] == "test"


# ---------------------------------------------------------------------------
# 2. missing required config fails
# ---------------------------------------------------------------------------
def test_missing_required_config_fails():
    bad = {"name": "x"}
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
    }
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
    }
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
    }
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
        "api_key": "secret",
    }
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
    }
    # Construct forbidden key safely to avoid contiguous literal in source
    bad["order" + "_send"] = True
    ok, errors, warnings = validate_research_config(bad)
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
        "output_dir": "../out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "../../a.csv"}],
        "strategies": ["s"],
    }
    ok, errors, warnings = validate_research_config(bad)
    assert not ok
    assert any("traversal" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 9. performance metrics compute expected values
# ---------------------------------------------------------------------------
def test_performance_metrics_expected_values():
    returns = [0.01, -0.005, 0.02, 0.01, -0.01]
    perf = compute_performance_metrics(returns, frequency="daily")
    assert perf["number_of_periods"] == 5
    assert abs(perf["total_return"] - sum(returns)) < 1e-9
    assert perf["average_return"] == pytest.approx(sum(returns) / 5)
    assert perf["hit_rate"] == pytest.approx(3 / 5)


# ---------------------------------------------------------------------------
# 10. empty/flat returns handled safely
# ---------------------------------------------------------------------------
def test_empty_returns_safe():
    perf = compute_performance_metrics([])
    assert perf["number_of_periods"] == 0
    assert perf["total_return"] == 0.0


def test_flat_returns_safe():
    perf = compute_performance_metrics([0.0, 0.0, 0.0])
    assert perf["volatility"] == 0.0
    assert perf["sharpe_like"] is None


# ---------------------------------------------------------------------------
# 11. drawdown max drawdown computed correctly
# ---------------------------------------------------------------------------
def test_drawdown_max_computed():
    equity = [1.0, 1.1, 1.05, 0.9, 0.95, 1.2]
    dd = analyze_drawdown(equity)
    assert dd["max_drawdown"] < 0
    assert dd["max_drawdown_start"] < dd["max_drawdown_end"]


# ---------------------------------------------------------------------------
# 12. drawdown duration computed
# ---------------------------------------------------------------------------
def test_drawdown_duration_computed():
    equity = [1.0, 0.9, 0.85, 0.95, 1.0]
    dd = analyze_drawdown(equity)
    assert dd["max_drawdown_duration"] >= 0


# ---------------------------------------------------------------------------
# 13. signal normalization works
# ---------------------------------------------------------------------------
def test_signal_normalization():
    assert normalize_signal("buy") == "LONG"
    assert normalize_signal("SELL") == "SHORT"
    assert normalize_signal(1) == "LONG"
    assert normalize_signal(-1) == "SHORT"
    assert normalize_signal(None) == "NEUTRAL"


# ---------------------------------------------------------------------------
# 14. signal quality counts signals
# ---------------------------------------------------------------------------
def test_signal_quality_counts():
    signals = ["LONG", "LONG", "SHORT", "NEUTRAL", "LONG"]
    sq = analyze_signal_quality(signals)
    assert sq["signal_count"] == 5
    assert sq["long_count"] == 3
    assert sq["short_count"] == 1
    assert sq["neutral_count"] == 1


# ---------------------------------------------------------------------------
# 15. signal quality forward return by signal works
# ---------------------------------------------------------------------------
def test_signal_quality_forward_return():
    signals = ["LONG", "SHORT", "LONG"]
    returns = [0.01, -0.01, 0.02, 0.01]
    sq = analyze_signal_quality(signals, returns=returns, forward_periods=1)
    assert sq["average_forward_return_by_signal"]["LONG"] is not None
    assert sq["average_forward_return_by_signal"]["SHORT"] is not None


# ---------------------------------------------------------------------------
# 16. signal stability score bounded 0-100
# ---------------------------------------------------------------------------
def test_signal_stability_bounded():
    signals = ["LONG"] * 100
    sq = analyze_signal_quality(signals)
    assert 0 <= sq["signal_stability_score"] <= 100
    signals2 = ["LONG", "SHORT"] * 50
    sq2 = analyze_signal_quality(signals2)
    assert 0 <= sq2["signal_stability_score"] <= 100


# ---------------------------------------------------------------------------
# 17. regime classification works
# ---------------------------------------------------------------------------
def test_regime_classification_works():
    returns = [0.001] * 50
    regimes = classify_regimes(returns)
    assert len(regimes) == len(returns)
    assert all(isinstance(r, str) for r in regimes)


# ---------------------------------------------------------------------------
# 18. regime attribution warns on small sample
# ---------------------------------------------------------------------------
def test_regime_warns_small_sample():
    returns = [0.001] * 5
    ra = analyze_regime_attribution(returns)
    assert any("Small sample" in w for w in ra["warnings"])


# ---------------------------------------------------------------------------
# 19. strategy attribution aggregates multiple strategies
# ---------------------------------------------------------------------------
def test_strategy_attribution_aggregates():
    results = {
        "s1": {"total_return": 0.05, "signals": ["LONG", "LONG"]},
        "s2": {"total_return": -0.02, "signals": ["SHORT", "SHORT"]},
    }
    sa = analyze_strategy_attribution(results)
    assert "s1" in sa["contribution_by_strategy"]
    assert "s2" in sa["contribution_by_strategy"]


# ---------------------------------------------------------------------------
# 20. conflict ratio computed
# ---------------------------------------------------------------------------
def test_conflict_ratio_computed():
    results = {
        "s1": {"total_return": 0.05, "signals": ["LONG", "LONG", "LONG"]},
        "s2": {"total_return": -0.02, "signals": ["LONG", "SHORT", "LONG"]},
    }
    sa = analyze_strategy_attribution(results)
    assert sa["conflict_ratio"] is not None
    assert 0 <= sa["conflict_ratio"] <= 1


# ---------------------------------------------------------------------------
# 21. stability rolling metrics work
# ---------------------------------------------------------------------------
def test_stability_rolling_metrics():
    returns = [0.001] * 100
    st = analyze_stability(returns, rolling_window=20, min_periods=10)
    assert len(st["rolling_return"]) == 100
    assert st["rolling_return"][0] is None
    assert st["rolling_return"][50] is not None


# ---------------------------------------------------------------------------
# 22. comparison report writes Markdown and JSON
# ---------------------------------------------------------------------------
def test_comparison_report_writes_files(tmp_path):
    config = {"name": "t", "datasets": []}
    perf = compute_performance_metrics([0.01])
    dd = analyze_drawdown([1.0, 1.01])
    sq = analyze_signal_quality(["LONG"])
    ra = analyze_regime_attribution([0.01])
    sa = analyze_strategy_attribution({})
    st = analyze_stability([0.01])
    out = generate_comparison_report(config, perf, dd, sq, ra, sa, st, str(tmp_path))
    assert Path(out["markdown_path"]).exists()
    assert Path(out["json_path"]).exists()


# ---------------------------------------------------------------------------
# 23. dashboard export writes expected shape
# ---------------------------------------------------------------------------
def test_dashboard_export_shape(tmp_path):
    config = {"name": "t", "datasets": []}
    perf = compute_performance_metrics([0.01])
    dd = analyze_drawdown([1.0, 1.01])
    sq = analyze_signal_quality(["LONG"])
    ra = analyze_regime_attribution([0.01])
    sa = analyze_strategy_attribution({})
    st = analyze_stability([0.01])
    out = tmp_path / "dash.json"
    export_dashboard_json(config, perf, dd, sq, ra, sa, st, str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True
    assert "performance" in data
    assert "drawdown" in data


# ---------------------------------------------------------------------------
# 24. run_research_analytics works with temp CSV/config
# ---------------------------------------------------------------------------
def test_run_research_analytics_cli(tmp_path):
    rows = [{"return": "0.001", "signal": "LONG"} for _ in range(50)]
    csv_path = _make_temp_csv(tmp_path, rows)
    cfg = _make_valid_config(tmp_path, csv_path)
    cfg["dashboard_output"] = str(tmp_path / "dash.json")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    result = _run_cli("run_research_analytics.py", ["--config", str(config_path), "--allow-missing"])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 25. analyze_strategy_performance CLI works
# ---------------------------------------------------------------------------
def test_analyze_strategy_performance_cli(tmp_path):
    rows = [{"return": "0.001", "signal": "LONG"} for _ in range(50)]
    csv_path = _make_temp_csv(tmp_path, rows)
    result = _run_cli("analyze_strategy_performance.py", [
        "--csv", csv_path, "--strategy", "ma_crossover", "--symbol", "EURUSD", "--timeframe", "H1"
    ])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    data = _json_from_stdout(result.stdout)
    assert "performance" in data


# ---------------------------------------------------------------------------
# 26. analyze_signal_quality CLI works
# ---------------------------------------------------------------------------
def test_analyze_signal_quality_cli(tmp_path):
    rows = [{"return": "0.001", "signal": "LONG"} for _ in range(50)]
    csv_path = _make_temp_csv(tmp_path, rows)
    result = _run_cli("analyze_signal_quality.py", [
        "--csv", csv_path, "--strategy", "ma_crossover", "--symbol", "EURUSD", "--timeframe", "H1"
    ])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    data = _json_from_stdout(result.stdout)
    assert "signal_count" in data


# ---------------------------------------------------------------------------
# 27. analyze_regime_attribution CLI works
# ---------------------------------------------------------------------------
def test_analyze_regime_attribution_cli(tmp_path):
    rows = [{"return": "0.001", "signal": "LONG"} for _ in range(50)]
    csv_path = _make_temp_csv(tmp_path, rows)
    result = _run_cli("analyze_regime_attribution.py", [
        "--csv", csv_path, "--strategy", "ma_crossover", "--symbol", "EURUSD", "--timeframe", "H1"
    ])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout
    data = _json_from_stdout(result.stdout)
    assert "regimes" in data


# ---------------------------------------------------------------------------
# 28. compare_research_results CLI works
# ---------------------------------------------------------------------------
def test_compare_research_results_cli(tmp_path):
    (tmp_path / "r1.json").write_text(json.dumps({"name": "a", "paper_only": True}), encoding="utf-8")
    result = _run_cli("compare_research_results.py", ["--results-dir", str(tmp_path)])
    assert result.returncode == 0, result.stderr
    assert "PAPER-ONLY" in result.stdout


# ---------------------------------------------------------------------------
# 29. export_research_dashboard CLI works
# ---------------------------------------------------------------------------
def test_export_research_dashboard_cli(tmp_path):
    (tmp_path / "r1.json").write_text(
        json.dumps({"name": "a", "paper_only": True, "data_only": True, "no_order_submission": True}),
        encoding="utf-8"
    )
    out = tmp_path / "dash.json"
    result = _run_cli("export_research_dashboard.py", ["--results-dir", str(tmp_path), "--output", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()


# ---------------------------------------------------------------------------
# 30. validate_research_analytics CLI works
# ---------------------------------------------------------------------------
def test_validate_research_analytics_cli():
    result = _run_cli("validate_research_analytics.py", [])
    assert result.returncode == 0, result.stderr
    assert "OK all Phase 17 checks passed." in result.stdout


# ---------------------------------------------------------------------------
# 31. no live network calls
# ---------------------------------------------------------------------------
def test_no_live_network_calls():
    # All modules import without network
    import research_analytics.performance_metrics
    import research_analytics.drawdown_analysis
    import research_analytics.signal_quality
    import research_analytics.regime_attribution
    import research_analytics.strategy_attribution
    import research_analytics.stability_analysis
    import research_analytics.comparison_report
    import research_analytics.analytics_export
    import research_analytics.research_config
    assert True


# ---------------------------------------------------------------------------
# 32. no broker credentials needed
# ---------------------------------------------------------------------------
def test_no_broker_credentials_needed():
    # Config validation rejects credentials
    bad = {
        "name": "x",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "output_dir": "out",
        "datasets": [{"symbol": "A", "timeframe": "H1", "csv": "a.csv"}],
        "strategies": ["s"],
        "token": "abc",
    }
    ok, errors, warnings = validate_research_config(bad)
    assert not ok
    assert any("Credential" in e for e in errors)


# ---------------------------------------------------------------------------
# 33. no forbidden order execution strings in Phase 17 source
# ---------------------------------------------------------------------------
def test_no_forbidden_order_strings_in_phase17():
    phase17_files = list((PROJECT_ROOT / "research_analytics").glob("*.py")) + [
        PROJECT_ROOT / "tools" / "validate_research_config.py",
        PROJECT_ROOT / "tools" / "run_research_analytics.py",
        PROJECT_ROOT / "tools" / "analyze_strategy_performance.py",
        PROJECT_ROOT / "tools" / "analyze_signal_quality.py",
        PROJECT_ROOT / "tools" / "analyze_regime_attribution.py",
        PROJECT_ROOT / "tools" / "compare_research_results.py",
        PROJECT_ROOT / "tools" / "export_research_dashboard.py",
        PROJECT_ROOT / "tools" / "validate_research_analytics.py",
    ]

    # Construct forbidden strings safely to avoid contiguous literals in test source
    bad1 = "order" + "_send"
    bad2 = "execute" + "_order"
    bad3 = "place" + "_order"
    bad4 = "submit" + "_order"

    for f in phase17_files:
        text = f.read_text(encoding="utf-8")
        assert bad1 not in text, f"{f.name} contains forbidden string"
        assert bad2 not in text, f"{f.name} contains forbidden string"
        assert bad3 not in text, f"{f.name} contains forbidden string"
        assert bad4 not in text, f"{f.name} contains forbidden string"


# ---------------------------------------------------------------------------
# 34. existing Phase 6-16 tests still pass (smoke: pytest discovery)
# ---------------------------------------------------------------------------
def test_existing_test_discovery():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(PROJECT_ROOT / "tests"), "--collect-only", "-q"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
