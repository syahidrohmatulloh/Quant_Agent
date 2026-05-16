import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.dashboard_validator import DashboardValidator
from main import app


class TestDashboardValidator:
    def test_all_dashboard_routes_pass(self):
        validator = DashboardValidator(app=app, viewer_token="viewer123")
        os.environ["DASHBOARD_AUTH_DISABLED"] = "true"
        result = validator.validate()
        del os.environ["DASHBOARD_AUTH_DISABLED"]
        assert result["valid"] is True
        assert "/dashboard/" in result["routes_checked"]
        assert "/dashboard/positions" in result["routes_checked"]
        assert "/dashboard/signals" in result["routes_checked"]
        assert "/dashboard/alerts" in result["routes_checked"]
        assert "/dashboard/models" in result["routes_checked"]
        assert "/dashboard/backtests" in result["routes_checked"]

    def test_secrets_not_exposed(self):
        validator = DashboardValidator(app=app, viewer_token="viewer123")
        os.environ["DASHBOARD_AUTH_DISABLED"] = "true"
        result = validator.validate()
        del os.environ["DASHBOARD_AUTH_DISABLED"]
        assert result["valid"] is True
        assert not any("secret" in e.lower() for e in result["errors"])

    def test_auth_required(self):
        validator = DashboardValidator(app=app)
        result = validator.validate()
        # Auth is enabled by default, so routes should fail without token
        assert not result["valid"] or any("auth" in e.lower() for e in result["errors"])

    def test_paper_only_text_visible(self):
        validator = DashboardValidator(app=app, viewer_token="viewer123")
        os.environ["DASHBOARD_AUTH_DISABLED"] = "true"
        result = validator.validate()
        del os.environ["DASHBOARD_AUTH_DISABLED"]
        assert result["paper_only_visible"] is True
