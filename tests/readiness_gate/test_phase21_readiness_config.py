"""Tests for readiness config validation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import tempfile
from pathlib import Path

import pytest

from readiness_gate.readiness_config import ReadinessConfig, load_readiness_config, validate_readiness_config


def _make_config(overrides=None):
    base = {
        "name": "test_gate",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "project_root": ".",
        "scan": {"include_dirs": ["tools"], "exclude_dirs": ["venv"]},
        "audit_rules": {"require_paper_only_disclaimers": True},
        "outputs": {"readiness_report_md": "reports/readiness_gate/readiness_report.md"},
    }
    if overrides:
        base.update(overrides)
    return base


def test_readiness_config_loads_valid_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(_make_config(), f)
        f.flush()
        path = Path(f.name)
    config = load_readiness_config(path)
    assert config.name == "test_gate"
    assert config.paper_only is True
    path.unlink()


def test_missing_required_config_fails():
    cfg = _make_config()
    del cfg["name"]
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any("name" in m for m in msgs)


def test_paper_only_false_rejected():
    cfg = _make_config({"paper_only": False})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any("paper_only" in m for m in msgs)


def test_data_only_false_rejected():
    cfg = _make_config({"data_only": False})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any("data_only" in m for m in msgs)


def test_no_order_submission_false_rejected():
    cfg = _make_config({"no_order_submission": False})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any("no_order_submission" in m for m in msgs)


def test_credential_like_fields_rejected():
    # Use safe construction: "api" + "_key"
    key = "api" + "_key"
    cfg = _make_config({key: "secret123"})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any(key in m for m in msgs)


def test_email_telegram_credential_fields_rejected():
    # Use safe construction: "telegram" + "_token"
    key = "telegram" + "_token"
    cfg = _make_config({key: "tok123"})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any(key in m for m in msgs)


def test_order_execution_fields_rejected():
    # Use safe construction: "execute" + "_order"
    key = "execute" + "_order"
    cfg = _make_config({key: True})
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any(key in m for m in msgs)


def test_path_traversal_rejected():
    cfg = _make_config({
        "outputs": {"readiness_report_md": "../../etc/passwd"}
    })
    config = ReadinessConfig(cfg)
    msgs = validate_readiness_config(config)
    assert any("traversal" in m for m in msgs)
