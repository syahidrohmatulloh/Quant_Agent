
import os
import pytest
from core.auth import get_role, ROLES

def test_auth_flow():
    os.environ["QUANT_VIEWER_TOKEN"] = "v123"
    os.environ["QUANT_OPERATOR_TOKEN"] = "o123"
    os.environ["QUANT_ADMIN_TOKEN"] = "a123"
    ROLES["viewer"] = "v123"
    ROLES["operator"] = "o123"
    ROLES["admin"] = "a123"
    assert get_role("v123") == "viewer"
    assert get_role("o123") == "operator"
    assert get_role("a123") == "admin"
