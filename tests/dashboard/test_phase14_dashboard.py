"""
Tests for Phase 14 dashboard module.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import tempfile
import csv
from pathlib import Path
from fastapi.testclient import TestClient

from dashboard.app import create_phase14_app


PHASE14_MODULES = [
    "dashboard/__init__.py",
    "dashboard/app.py",
    "dashboard/routes.py",
    "dashboard/templates.py",
    "dashboard/static_assets.py",
    "dashboard/data_access.py",
    "dashboard/view_models.py",
    "dashboard/safety.py",
]


@pytest.fixture
def client():
    app = create_phase14_app()
    return TestClient(app)


def test_health_route_returns_ok_and_paper_only(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["paper_only"] is True
    assert data["data_only"] is True
    assert data["no_order_submission"] is True


def test_home_page_contains_paper_only_disclaimer(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PAPER-ONLY" in response.text
    assert "DATA-ONLY" in response.text


def test_datasets_page_works_with_temp_csv(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        market_dir = Path(tmpdir) / "data" / "market"
        market_dir.mkdir(parents=True, exist_ok=True)
        csv_path = market_dir / "mt5_EURUSD_H1.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "tick_volume"])
            writer.writerow(["2024.01.15 10:00", "1.1000", "1.1005", "1.0995", "1.1002", "1000"])

        from dashboard import data_access
        orig_root = data_access.get_project_root
        data_access.get_project_root = lambda: Path(tmpdir)
        try:
            response = client.get("/datasets")
            assert response.status_code == 200
            assert "EURUSD" in response.text or "mt5_EURUSD_H1.csv" in response.text
        finally:
            data_access.get_project_root = orig_root


def test_dataset_detail_rejects_path_traversal(client):
    response = client.get("/datasets/../../../etc/passwd")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "etc_passwd" in response.text or "not found" in response.text.lower()


def test_reports_page_works_with_temp_report(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        reports_dir = os.path.join(tmpdir, "reports", "experiments")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "test_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Test Report\n\nGenerated: 2024-01-15T10:00:00Z\n")

        from dashboard import data_access
        orig_root = data_access.get_project_root
        data_access.get_project_root = lambda: Path(tmpdir)
        try:
            response = client.get("/reports")
            assert response.status_code == 200
            assert "Test Report" in response.text
        finally:
            data_access.get_project_root = orig_root


def test_report_detail_escapes_html(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        reports_dir = os.path.join(tmpdir, "reports", "experiments")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "evil.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("<script>alert('xss')</script>")

        from dashboard import data_access
        orig_root = data_access.get_project_root
        data_access.get_project_root = lambda: Path(tmpdir)
        try:
            response = client.get("/reports/evil.md")
            assert response.status_code == 200
            assert "<script>" not in response.text
            assert "&lt;script&gt;" in response.text
        finally:
            data_access.get_project_root = orig_root


def test_latest_dashboard_json_route_handles_missing_files(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        from dashboard import data_access
        orig_root = data_access.get_project_root
        data_access.get_project_root = lambda: Path(tmpdir)
        try:
            response = client.get("/dashboard/latest")
            assert response.status_code == 200
            assert "No dashboard JSON" in response.text or "dashboard json" in response.text.lower()
        finally:
            data_access.get_project_root = orig_root


def test_experiment_history_handles_empty_directory(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        from dashboard import data_access
        orig_root = data_access.get_project_root
        data_access.get_project_root = lambda: Path(tmpdir)
        try:
            response = client.get("/experiments/history")
            assert response.status_code == 200
            assert "No experiment history" in response.text or "history" in response.text.lower()
        finally:
            data_access.get_project_root = orig_root


def test_dashboard_data_access_only_reads_allowed_dirs():
    from dashboard.safety import is_under_allowed_root
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "data" / "market").mkdir(parents=True)
        (root / "examples").mkdir(parents=True)
        (root / "reports" / "experiments").mkdir(parents=True)
        (root / "reports" / "dashboard" / "experiments").mkdir(parents=True)
        (root / "reports" / "experiments" / "history").mkdir(parents=True)

        assert is_under_allowed_root(str(root / "data" / "market" / "foo.csv"), str(root))
        assert is_under_allowed_root(str(root / "examples" / "config.json"), str(root))
        assert is_under_allowed_root(str(root / "reports" / "experiments" / "report.md"), str(root))

        assert not is_under_allowed_root(str(root / ".env"), str(root))
        assert not is_under_allowed_root(str(root / "secrets" / "key.pem"), str(root))
        assert not is_under_allowed_root("/etc/passwd", str(root))


def test_no_live_trading_calls_in_dashboard_modules():
    project_root = Path(__file__).resolve().parents[2]
    forbidden = [
        "order" + "_send",
        "execute" + "_order",
        "place" + "_order",
        "submit" + "_order",
    ]
    for rel in PHASE14_MODULES:
        p = project_root / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8").lower()
        for f in forbidden:
            assert f not in content, f"{rel} contains {f}"


def test_no_credential_form_fields():
    project_root = Path(__file__).resolve().parents[2]
    forbidden = [
        'type="' + 'password"',
        "type='" + "password'",
    ]
    for rel in PHASE14_MODULES:
        p = project_root / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8").lower()
        for f in forbidden:
            assert f not in content, f"{rel} contains credential input"


def test_no_external_cdn_or_remote_scripts():
    from dashboard.static_assets import INLINE_CSS
    lowered = INLINE_CSS.lower()
    cdn_indicators = [
        "cdnjs.cloudflare.com", "unpkg.com", "jsdelivr.net",
        "bootstrapcdn.com", "googleapis.com", "jquery.com",
    ]
    for cdn in cdn_indicators:
        assert cdn not in lowered, f"INLINE_CSS references external CDN: {cdn}"
    assert "<script" not in lowered, "INLINE_CSS contains script tag"


def test_no_live_broker_calls_in_dashboard():
    project_root = Path(__file__).resolve().parents[2]
    for rel in PHASE14_MODULES:
        p = project_root / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8").lower()
        assert "urllib" not in content, f"{rel} uses urllib"
        assert "requests" not in content, f"{rel} uses requests"
        assert "socket" not in content, f"{rel} uses socket"
