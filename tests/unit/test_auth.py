
import os
import pytest
from core.auth import get_role, ROLES

@pytest.fixture(autouse=True)
def setup_tokens(monkeypatch):
    monkeypatch.setenv("QUANT_VIEWER_TOKEN", "viewer_token_123")
    monkeypatch.setenv("QUANT_OPERATOR_TOKEN", "operator_token_123")
    monkeypatch.setenv("QUANT_ADMIN_TOKEN", "admin_token_123")
    ROLES["viewer"] = "viewer_token_123"
    ROLES["operator"] = "operator_token_123"
    ROLES["admin"] = "admin_token_123"

def test_get_role_viewer():
    assert get_role("viewer_token_123") == "viewer"

def test_get_role_operator():
    assert get_role("operator_token_123") == "operator"

def test_get_role_admin():
    assert get_role("admin_token_123") == "admin"

def test_get_role_invalid():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        get_role("bad_token")

def test_roles_length():
    assert len(ROLES) == 3
