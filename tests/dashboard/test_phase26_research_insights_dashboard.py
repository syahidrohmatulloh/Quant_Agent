"""Tests for Phase 26 research insights dashboard page.

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


def test_research_insights_route_exists(client):
    response = client.get("/research-insights")
    assert response.status_code == 200


def test_research_insights_contains_paper_only_disclaimer(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "PAPER-ONLY" in response.text
    assert "DATA-ONLY" in response.text


def test_research_insights_contains_not_financial_advice(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "not financial advice" in response.text.lower()


def test_research_insights_contains_strategy_comparison_header(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "Strategy Comparison" in response.text


def test_research_insights_contains_next_safe_commands(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "Next Safe Commands" in response.text


def test_research_insights_contains_no_live_trading(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "No live trading" in response.text or "no live trading" in response.text.lower()


def test_research_insights_shows_no_outputs_message_when_empty(client):
    response = client.get("/research-insights")
    assert response.status_code == 200
    assert "No research outputs found yet" in response.text or "No strategy outputs found" in response.text


def test_health_route_unchanged(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True


def test_datasets_route_unchanged(client):
    response = client.get("/datasets")
    assert response.status_code == 200


def test_reports_route_unchanged(client):
    response = client.get("/reports")
    assert response.status_code == 200


def test_dashboard_latest_route_unchanged(client):
    response = client.get("/dashboard/latest")
    assert response.status_code == 200


def test_operator_route_unchanged(client):
    response = client.get("/operator")
    assert response.status_code == 200


def test_action_center_route_unchanged(client):
    response = client.get("/action-center")
    assert response.status_code == 200


def test_home_page_links_to_research_insights(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "research-insights" in response.text.lower()


def test_operator_page_links_to_research_insights(client):
    response = client.get("/operator")
    assert response.status_code == 200
    assert "research-insights" in response.text.lower()


def test_action_center_page_links_to_research_insights(client):
    response = client.get("/action-center")
    assert response.status_code == 200
    assert "research-insights" in response.text.lower()
