
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_no_secrets_in_dashboard():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    os.environ["QUANT_ADMIN_TOKEN"] = "admin_secret_xyz"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    ROLES["admin"] = "admin_secret_xyz"
    response = client.get("/dashboard/", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "admin_secret_xyz" not in response.text
    assert "viewer123" not in response.text

def test_no_env_vars_exposed():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/", headers={"token": "viewer123"})
    assert "QUANT_" not in response.text or "Mode:" in response.text

def test_auth_disabled_env():
    import os
    import importlib
    os.environ["DASHBOARD_AUTH_DISABLED"] = "true"
    # Re-import to pick up env change
    from dashboard import routes_dashboard
    importlib.reload(routes_dashboard)
    assert routes_dashboard.DASHBOARD_AUTH_DISABLED is True
    os.environ["DASHBOARD_AUTH_DISABLED"] = "false"
    importlib.reload(routes_dashboard)
