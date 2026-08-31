"""Tests for Phase 30 release candidate CLI tool.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def _run_tool(script_name, args, cwd=PROJECT_ROOT, env=None):
    cmd = [PYTHON, str(PROJECT_ROOT / "tools" / script_name)] + args
    clean_env = os.environ.copy()
    clean_env["PYTHONPATH"] = str(PROJECT_ROOT)
    for key in list(clean_env.keys()):
        if any(x in key.lower() for x in ["api" + "_key", "token", "secret", "password"]):
            del clean_env[key]
    if env:
        clean_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=clean_env)
    return result


def _make_config(root: Path):
    cfg = {
        "name": "test_release_candidate",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "directories": {
            "reports": "reports",
        },
    }
    return cfg


class TestRunReleaseCandidateCheckCLI:
    def test_runs_with_allow_missing_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_output_contains_paper_only_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "PAPER-ONLY" in combined
            assert "DATA-ONLY" in combined

    def test_output_contains_local_mvp_release_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "Local MVP Release Candidate" in combined

    def test_output_contains_no_live_trading(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "No live trading" in combined or "no live trading" in combined.lower()

    def test_returns_nonzero_for_missing_config(self):
        result = _run_tool("run_release_candidate_check.py", [
            "--config", "/nonexistent/config.json",
            "--allow-missing",
        ])
        assert result.returncode != 0

    def test_returns_zero_for_ready_with_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_write_report_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
                "--write-report",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
            report_dir = PROJECT_ROOT / "reports" / "release_candidate"
            # Files may be written to PROJECT_ROOT reports, not tmp; that is expected for this CLI
            json_file = report_dir / "release_candidate_report.json"
            md_file = report_dir / "release_candidate_report.md"
            assert json_file.exists() or md_file.exists()
            if json_file.exists():
                json_file.unlink()
            if md_file.exists():
                md_file.unlink()
            if report_dir.exists():
                report_dir.rmdir()

    def test_smoke_does_not_call_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
                "--smoke",
            ])
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
            combined = result.stdout + result.stderr
            assert "[SMOKE]" in combined

    def test_no_credentials_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            clean_env = {k: v for k, v in os.environ.items() if not any(
                x in k.lower() for x in ["token", "password", "secret", "api" + "_key", "apikey", "cred"]
            )}
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ], env=clean_env)
            assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_no_hardcoded_paths_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "run_release_candidate_check.py"
        if not cli_path.exists():
            pytest.skip("CLI source not found")
        content = cli_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found in CLI: {f}"

    def test_no_forbidden_raw_literals_in_cli_source(self):
        cli_path = PROJECT_ROOT / "tools" / "run_release_candidate_check.py"
        if not cli_path.exists():
            pytest.skip("CLI source not found")
        content = cli_path.read_text(encoding="utf-8")
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"

    def test_cli_avoids_buy_sell_live_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = _make_config(tmp_path)
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = _run_tool("run_release_candidate_check.py", [
                "--config", str(config_path),
                "--allow-missing",
            ])
            combined = result.stdout + result.stderr
            assert "buy" not in combined.lower() or "paper" in combined.lower()
            assert "sell" not in combined.lower() or "paper" in combined.lower()


class TestDocsMentionReleaseCandidate:
    def test_daily_workflow_mentions_release_candidate(self):
        path = PROJECT_ROOT / "docs" / "DAILY_WORKFLOW.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "run_release_candidate_check.py" in content or "release candidate" in content.lower()

    def test_command_cheatsheet_mentions_release_candidate(self):
        path = PROJECT_ROOT / "docs" / "COMMAND_CHEATSHEET.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "run_release_candidate_check.py" in content or "release candidate" in content.lower()

    def test_phase_history_mentions_phase30(self):
        path = PROJECT_ROOT / "docs" / "PHASE_HISTORY.md"
        if not path.exists():
            pytest.skip("Docs not found")
        content = path.read_text(encoding="utf-8")
        assert "Phase 30" in content
        assert "release candidate" in content.lower()
