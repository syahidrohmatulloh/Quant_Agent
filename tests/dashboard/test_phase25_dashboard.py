"""Tests for Phase 25 dashboard action center page.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from dashboard.app import create_phase14_app

@pytest.fixture
def client():
    app = create_phase14_app()
    return TestClient(app)

def test_action_center_route_exists(client):
    response = client.get("/action-center")
    assert response.status_code == 200

def test_action_center_contains_paper_only_disclaimer(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "PAPER-ONLY" in response.text
    assert "DATA-ONLY" in response.text

def test_action_center_contains_overall_status(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Overall:" in response.text

def test_action_center_contains_warning_categories(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    # Should contain category headers or "No categorized warnings"
    assert "Warning Categories" in response.text

def test_action_center_contains_blockers_section(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Blockers" in response.text

def test_action_center_contains_warnings_section(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Warnings" in response.text

def test_action_center_contains_action_items_section(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Action Items" in response.text

def test_action_center_contains_next_safe_commands(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Next Safe Commands" in response.text

def test_action_center_contains_readiness_section(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "Readiness" in response.text

def test_operator_page_links_to_action_center(client):
    response = client.get("/operator")
    assert response.status_code == 200
    assert "action-center" in response.text.lower() or "Action Center" in response.text

def test_health_route_unchanged(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True
