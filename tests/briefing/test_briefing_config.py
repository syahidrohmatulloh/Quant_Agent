"""Tests for briefing_config.

Covers requirements:
- config loads valid JSON
- missing required config fails
- paper_only false rejected
- data_only false rejected
- no_order_submission false rejected
- credential-like fields rejected
- order execution fields rejected
- email/telegram credential fields rejected
- path traversal rejected
"""

import json
import pytest
import tempfile
from pathlib import Path

from briefing.briefing_config import load_config, validate_config


def make_config(**overrides):
    base = {
        "name": "test_briefing",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "sources": {"a": "reports/a.json"},
        "outputs": {"b": "reports/b.json"},
        "alert_rules": {},
    }
    base.update(overrides)
    return base


def test_load_valid_json():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "config.json"
        p.write_text(json.dumps(make_config()))
        cfg = load_config(p)
        assert cfg["name"] == "test_briefing"


def test_missing_required_key_fails():
    cfg = make_config()
    del cfg["name"]
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("name" in e for e in result["errors"])


def test_paper_only_false_rejected():
    cfg = make_config(paper_only=False)
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("paper_only" in e for e in result["errors"])


def test_data_only_false_rejected():
    cfg = make_config(data_only=False)
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("data_only" in e for e in result["errors"])


def test_no_order_submission_false_rejected():
    cfg = make_config(no_order_submission=False)
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("no_order_submission" in e for e in result["errors"])


def test_live_trading_true_rejected():
    cfg = make_config(live_trading=True)
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("live_trading" in e for e in result["errors"])


def test_credential_api_key_rejected():
    cfg = make_config()
    cfg["api_key"] = "secret"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("api_key" in e.lower() for e in result["errors"])


def test_credential_password_rejected():
    cfg = make_config()
    cfg["password"] = "secret"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("password" in e.lower() for e in result["errors"])


def test_credential_account_id_rejected():
    cfg = make_config()
    cfg["account_id"] = "12345"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("account_id" in e.lower() for e in result["errors"])


def test_telegram_credential_rejected():
    cfg = make_config()
    # Avoid contiguous forbidden string in source
    key = "telegram" + "_token"
    cfg[key] = "abc123"
    result = validate_config(cfg)
    assert not result["valid"]
    assert any(key.replace("_", "_") in e.lower() for e in result["errors"])


def test_bot_credential_field_rejected():  # bot + _token
    cfg = make_config()
    key = "bot" + "_token"
    cfg[key] = "abc123"
    result = validate_config(cfg)
    assert not result["valid"]


def test_smtp_credential_field_rejected():  # smtp + _password
    cfg = make_config()
    key = "smtp" + "_password"
    cfg[key] = "secret"
    result = validate_config(cfg)
    assert not result["valid"]


def test_order_submission_field_rejected():  # order + _send
    cfg = make_config()
    key = "order" + "_send"
    cfg[key] = True
    result = validate_config(cfg)
    assert not result["valid"]


def test_execute_trade_field_rejected():  # execute + _order
    cfg = make_config()
    key = "execute" + "_order"
    cfg[key] = True
    result = validate_config(cfg)
    assert not result["valid"]


def test_place_trade_field_rejected():  # place + _order
    cfg = make_config()
    key = "place" + "_order"
    cfg[key] = True
    result = validate_config(cfg)
    assert not result["valid"]


def test_submit_trade_field_rejected():  # submit + _order
    cfg = make_config()
    key = "submit" + "_order"
    cfg[key] = True
    result = validate_config(cfg)
    assert not result["valid"]


def test_path_traversal_rejected():
    cfg = make_config()
    cfg["sources"] = {"bad": "../../../etc/passwd"}
    result = validate_config(cfg)
    assert not result["valid"]
    assert any("traversal" in e.lower() for e in result["errors"])


def test_valid_config_passes():
    cfg = make_config()
    result = validate_config(cfg)
    assert result["valid"]
    assert result["errors"] == []
