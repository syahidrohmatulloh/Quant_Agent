
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_dashboard_index_requires_auth():
    response = client.get("/dashboard/")
    assert response.status_code == 401

def test_dashboard_positions_requires_auth():
    response = client.get("/dashboard/positions")
    assert response.status_code == 401

def test_dashboard_signals_requires_auth():
    response = client.get("/dashboard/signals")
    assert response.status_code == 401

def test_dashboard_alerts_requires_auth():
    response = client.get("/dashboard/alerts")
    assert response.status_code == 401

def test_dashboard_models_requires_auth():
    response = client.get("/dashboard/models")
    assert response.status_code == 401

def test_dashboard_backtests_requires_auth():
    response = client.get("/dashboard/backtests")
    assert response.status_code == 401

def test_dashboard_index_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Quant Platform Dashboard" in response.text

def test_dashboard_positions_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/positions", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Paper Positions" in response.text

def test_dashboard_signals_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/signals", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Signals" in response.text

def test_dashboard_alerts_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/alerts", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Alerts" in response.text

def test_dashboard_models_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/models", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Models" in response.text

def test_dashboard_backtests_with_viewer_token():
    import os
    os.environ["QUANT_VIEWER_TOKEN"] = "viewer123"
    from core.auth import ROLES
    ROLES["viewer"] = "viewer123"
    response = client.get("/dashboard/backtests", headers={"token": "viewer123"})
    assert response.status_code == 200
    assert "Backtests" in response.text
