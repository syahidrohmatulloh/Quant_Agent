"""Tests for Phase 28 data quality dashboard page.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_phase14_app


@pytest.fixture
def client():
    app = create_phase14_app()
    return TestClient(app)


def test_data_quality_route_exists(client):
    response = client.get("/data-quality")
    assert response.status_code == 200


def test_data_quality_contains_paper_only_disclaimer(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "PAPER-ONLY" in response.text
    assert "DATA-ONLY" in response.text


def test_data_quality_contains_not_financial_advice(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "not financial advice" in response.text.lower()


def test_data_quality_contains_data_quality_header(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "Data Quality" in response.text


def test_data_quality_contains_next_safe_commands(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "Next Safe Commands" in response.text


def test_data_quality_contains_no_live_trading(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "No live trading" in response.text or "no live trading" in response.text.lower()


def test_data_quality_shows_empty_when_no_outputs(client):
    response = client.get("/data-quality")
    assert response.status_code == 200
    assert "No files scanned" in response.text or "No market data import config" in response.text


def test_health_route_unchanged(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True


def test_home_page_links_to_data_quality(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "data-quality" in response.text.lower()


def test_operator_page_links_to_data_quality(client):
    response = client.get("/operator")
    assert response.status_code == 200
    assert "data-quality" in response.text.lower()


def test_action_center_page_links_to_data_quality(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "data-quality" in response.text.lower()


def test_research_insights_page_links_to_data_quality(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "data-quality" in response.text.lower()


def test_paper_runtime_page_links_to_data_quality(client):
    response = client.get("/paper-runtime")
    assert response.status_code == 200
    assert "data-quality" in response.text.lower()
