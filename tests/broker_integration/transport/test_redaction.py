"""Tests for redaction utilities."""
from broker_integration.transport.redaction import (
    mask_account_id, redact_token, redact_headers, redact_url, redact_secrets,
)


def test_mask_account_id():
    assert mask_account_id("1234567890") == "****7890"
    assert mask_account_id("1234") == "****"
    assert mask_account_id("") == "****"


def test_redact_token():
    assert redact_token("abcdef1234567890") == "abcd****7890"
    assert redact_token("short") == "****"


def test_redact_headers():
    headers = {"Authorization": "Bearer secret123", "Content-Type": "application/json"}
    redacted = redact_headers(headers)
    assert "secret123" not in redacted["Authorization"]
    assert redacted["Content-Type"] == "application/json"


def test_redact_url():
    url = "https://api.example.com?api_key=secret&symbol=EURUSD"
    redacted = redact_url(url)
    assert "secret" not in redacted
    assert "symbol=EURUSD" in redacted


def test_redact_secrets_nested():
    obj = {"api_key": "secret", "data": {"token": "tok"}, "list": [{"password": "pwd"}]}
    result = redact_secrets(obj)
    assert "secret" not in result["api_key"]
    assert "tok" not in result["data"]["token"]
    assert "pwd" not in result["list"][0]["password"]
