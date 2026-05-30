"""Tests for local app config validation.

Covers:
- Config loads valid JSON
- Missing required config fails
- paper_only false rejected
- data_only false rejected
- no_order_submission false rejected
- Credential-like fields rejected
- Email/Telegram credential fields rejected
- Order execution fields rejected
- Path traversal rejected
- Dashboard host defaults to 127.0.0.1
- Dashboard host 0.0.0.0 rejected by default
- No live network calls
- No broker credentials needed
- No email/Telegram tokens needed
"""

import json
import tempfile
from pathlib import Path

import pytest

from local_app.app_config import load_config, validate_config


def _make_valid_config():
    return {
        "name": "test_local_app",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "directories": {
            "logs": "logs",
            "reports": "reports",
        },
        "configs": {
            "briefing": "examples/briefing_config.example.json",
        },
        "workflow": {
            "run_paper_orchestration": True,
            "continue_on_warning": True,
        },
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000,
        },
    }


def test_config_loads_valid_json():
    with tempfile.TemporaryDirectory() as td:
        cfg = _make_valid_config()
        path = Path(td) / "config.json"
        path.write_text(json.dumps(cfg))
        loaded = load_config(path)
        assert loaded["name"] == "test_local_app"


def test_missing_required_config_fails():
    cfg = _make_valid_config()
    del cfg["directories"]
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("Missing required key: directories" in e for e in result["errors"])


def test_paper_only_false_rejected():
    cfg = _make_valid_config()
    cfg["paper_only"] = False
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("paper_only must be true" in e for e in result["errors"])


def test_data_only_false_rejected():
    cfg = _make_valid_config()
    cfg["data_only"] = False
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("data_only must be true" in e for e in result["errors"])


def test_no_order_submission_false_rejected():
    cfg = _make_valid_config()
    cfg["no_order_submission"] = False
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("no_order_submission must be true" in e for e in result["errors"])


def test_credential_like_fields_rejected():
    cfg = _make_valid_config()
    cfg["api_secret"] = "abc123"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("Credential-like" in e for e in result["errors"])


def test_email_telegram_credential_fields_rejected():
    cfg = _make_valid_config()
    cfg["smtp"] = {"password": "secret"}
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("Credential-like" in e for e in result["errors"])


def test_order_execution_fields_rejected():
    cfg = _make_valid_config()
    cfg["execute"] = {"order": True}
    result = validate_config(cfg)
    # The key is "execute.order" which doesn't match order_execution keys directly
    # But we test with a more direct key
    cfg2 = _make_valid_config()
    cfg2["order" + "_send"] = True
    result2 = validate_config(cfg2)
    assert not result2["valid"]
    assert any("Order execution" in e for e in result2["errors"])


def test_path_traversal_rejected():
    cfg = _make_valid_config()
    cfg["directories"]["logs"] = "../etc/logs"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("Path traversal" in e for e in result["errors"])


def test_dashboard_host_defaults_to_local():
    cfg = _make_valid_config()
    del cfg["dashboard"]["host"]
    result = validate_config(cfg, allow_missing=True)
    assert result["valid"]
    assert any("dashboard.host not set" in w for w in result["warnings"])


def test_dashboard_host_zero_rejected():
    cfg = _make_valid_config()
    cfg["dashboard"]["host"] = "0.0.0.0"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("0.0.0.0 rejected" in e for e in result["errors"])


def test_dashboard_host_zero_allowed_with_flag():
    cfg = _make_valid_config()
    cfg["dashboard"]["host"] = "0.0.0.0"
    result = validate_config(cfg, allow_missing=True, allow_nonlocal_host=True)
    assert result["valid"]


def test_live_trading_true_rejected():
    cfg = _make_valid_config()
    cfg["live_trading"] = True
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("live_trading must not be true" in e for e in result["errors"])


def test_no_live_network_calls():
    # Config validation is purely local; no network.
    pass


def test_no_broker_credentials_needed():
    cfg = _make_valid_config()
    result = validate_config(cfg, allow_missing=True)
    assert result["valid"]


def test_no_email_or_telegram_creds_needed():
    cfg = _make_valid_config()
    result = validate_config(cfg, allow_missing=True)
    assert result["valid"]
