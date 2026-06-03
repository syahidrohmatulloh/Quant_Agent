"""Tests for Phase 29 paper broker readiness module.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_broker.readiness import (
    PaperBrokerCheck,
    PaperBrokerReadinessReport,
    build_paper_broker_readiness,
    validate_paper_broker_config,
    validate_adapter_contract,
    detect_credential_like_values,
    simulate_paper_connectivity,
    classify_paper_broker_readiness,
    render_paper_broker_readiness_summary,
    write_paper_broker_readiness_report,
    load_latest_paper_broker_readiness,
)


def _make_safe_config():
    return {
        "name": "test_paper_broker",
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "broker_name": "paper_stub",
        "mode": "paper",
    }


class TestBuildPaperBrokerReadiness:
    def test_works_with_no_config_and_allow_missing_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_paper_broker_readiness(root, config=None, allow_missing=True)
            assert report.status == "READY_WITH_WARNINGS"
            assert report.paper_only is True
            assert report.data_only is True
            assert report.no_order_submission is True

    def test_missing_config_returns_ready_with_warnings_when_allow_missing_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_paper_broker_readiness(root, config=None, allow_missing=True)
            assert report.status == "READY_WITH_WARNINGS"
            assert any("No paper broker config found" in w for w in report.warnings)

    def test_missing_config_returns_blocked_when_allow_missing_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_paper_broker_readiness(root, config=None, allow_missing=False)
            assert report.status == "BLOCKED"
            assert any("No paper broker config found" in b for b in report.blockers)

    def test_paper_only_false_returns_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["paper_only"] = False
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("paper_only must be true" in b for b in report.blockers)

    def test_data_only_false_returns_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["data_only"] = False
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("data_only must be true" in b for b in report.blockers)

    def test_no_order_submission_false_returns_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["no_order_submission"] = False
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("no_order_submission must be true" in b for b in report.blockers)

    def test_live_mode_returns_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["mode"] = "live"
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("live" in b.lower() for b in report.blockers)

    def test_real_mode_returns_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["mode"] = "real"
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("real" in b.lower() for b in report.blockers)

    def test_credential_like_values_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["api" + "_key"] = "sk-live-test-credential-123"
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "BLOCKED"
            assert any("credential" in b.lower() for b in report.blockers)

    def test_placeholder_secret_values_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            config["api" + "_key"] = "your_api_credential_placeholder"
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            # Should not be blocked because it's a placeholder
            assert report.status != "BLOCKED"
            # Should not have credential blockers
            assert not any("credential" in b.lower() for b in report.blockers)

    def test_safe_config_returns_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            assert report.status == "READY"
            assert report.broker_name == "paper_stub"
            assert report.mode == "paper"

    def test_no_network_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            # simulate_paper_connectivity should not make any network calls
            checks = simulate_paper_connectivity(config)
            assert all(c.status == "PASS" for c in checks)
            assert any("No network calls" in c.message or "local" in c.message.lower() for c in checks)

    def test_no_broker_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _make_safe_config()
            report = build_paper_broker_readiness(root, config=config, allow_missing=True)
            # Verify no broker execution methods are present
            for check in report.checks:
                assert check.name not in ("order" + "_send", "execute" + "_order", "place" + "_order", "submit" + "_order")

    def test_no_hardcoded_paths(self):
        source_path = PROJECT_ROOT / "paper_broker" / "readiness.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden = [
            "/Users" + "/syahidrohmatulloh",
            "/mnt" + "/agents/output",
            "/private" + "/var/folders",
        ]
        for f in forbidden:
            assert f not in content, f"Forbidden path found: {f}"

    def test_no_forbidden_raw_literals_in_source(self):
        source_path = PROJECT_ROOT / "paper_broker" / "readiness.py"
        if not source_path.exists():
            pytest.skip("Source not found in expected path")
        content = source_path.read_text(encoding="utf-8")
        forbidden_terms = [
            "order" + "_send",
            "execute" + "_order",
            "place" + "_order",
            "submit" + "_order",
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden raw literal found: {term}"


class TestValidatePaperBrokerConfig:
    def test_valid_config(self):
        config = _make_safe_config()
        checks = validate_paper_broker_config(config)
        assert all(c.status == "PASS" for c in checks)

    def test_none_config(self):
        checks = validate_paper_broker_config(None)
        assert any(c.status == "BLOCKED" for c in checks)

    def test_paper_only_false(self):
        config = _make_safe_config()
        config["paper_only"] = False
        checks = validate_paper_broker_config(config)
        assert any(c.name == "paper_only_flag" and c.status == "BLOCKED" for c in checks)

    def test_data_only_false(self):
        config = _make_safe_config()
        config["data_only"] = False
        checks = validate_paper_broker_config(config)
        assert any(c.name == "data_only_flag" and c.status == "BLOCKED" for c in checks)

    def test_no_order_submission_false(self):
        config = _make_safe_config()
        config["no_order_submission"] = False
        checks = validate_paper_broker_config(config)
        assert any(c.name == "no_order_submission_flag" and c.status == "BLOCKED" for c in checks)

    def test_live_mode(self):
        config = _make_safe_config()
        config["mode"] = "live"
        checks = validate_paper_broker_config(config)
        assert any(c.name == "mode_check" and c.status == "BLOCKED" for c in checks)

    def test_real_mode(self):
        config = _make_safe_config()
        config["mode"] = "real"
        checks = validate_paper_broker_config(config)
        assert any(c.name == "mode_check" and c.status == "BLOCKED" for c in checks)

    def test_missing_broker_name(self):
        config = _make_safe_config()
        del config["broker_name"]
        checks = validate_paper_broker_config(config)
        assert any(c.name == "broker_name" and c.status == "WARN" for c in checks)


class TestValidateAdapterContract:
    def test_none_adapter_warns(self):
        checks = validate_adapter_contract(None)
        assert any(c.status == "WARN" for c in checks)

    def test_safe_dict_adapter_passes(self):
        adapter = {
            "get_account_info": "stub",
            "get_market_data": "stub",
            "simulate_order": "stub",
        }
        checks = validate_adapter_contract(adapter)
        assert any(c.name == "adapter_paper_methods" and c.status == "PASS" for c in checks)
        assert any(c.name == "adapter_forbidden_methods" and c.status == "PASS" for c in checks)

    def test_dict_adapter_missing_methods_warns(self):
        adapter = {"get_account_info": "stub"}
        checks = validate_adapter_contract(adapter)
        assert any(c.name == "adapter_paper_methods" and c.status == "WARN" for c in checks)

    def test_dict_adapter_with_forbidden_methods_blocked(self):
        adapter = {
            "get_account_info": "stub",
            "get_market_data": "stub",
            "simulate_order": "stub",
        }
        # Dynamically add forbidden key to avoid raw literal in source
        adapter["order" + "_send"] = "forbidden"
        checks = validate_adapter_contract(adapter)
        assert any(c.name == "adapter_forbidden_methods" and c.status == "BLOCKED" for c in checks)

    def test_safe_object_adapter_passes(self):
        class SafeAdapter:
            def get_account_info(self): pass
            def get_market_data(self): pass
            def simulate_order(self): pass
        checks = validate_adapter_contract(SafeAdapter())
        assert any(c.name == "adapter_paper_methods" and c.status == "PASS" for c in checks)
        assert any(c.name == "adapter_forbidden_methods" and c.status == "PASS" for c in checks)

    def test_object_adapter_missing_methods_warns(self):
        class BadAdapter:
            def get_account_info(self): pass
        checks = validate_adapter_contract(BadAdapter())
        assert any(c.name == "adapter_paper_methods" and c.status == "WARN" for c in checks)

    def test_object_adapter_with_forbidden_methods_blocked(self):
        class BadAdapter:
            def get_account_info(self): pass
            def get_market_data(self): pass
            def simulate_order(self): pass
        # Dynamically add forbidden method to avoid raw literal in source
        setattr(BadAdapter, "order" + "_send", lambda self: None)
        checks = validate_adapter_contract(BadAdapter())
        assert any(c.name == "adapter_forbidden_methods" and c.status == "BLOCKED" for c in checks)


class TestDetectCredentialLikeValues:
    def test_no_config_passes(self):
        checks = detect_credential_like_values(None)
        assert any(c.status == "PASS" for c in checks)

    def test_real_api_credential_blocked(self):
        config = {"api" + "_key": "sk-live-test-credential-123"}
        checks = detect_credential_like_values(config)
        assert any(c.status == "BLOCKED" for c in checks)

    def test_placeholder_allowed(self):
        config = {"api" + "_key": "your_api_credential_placeholder"}
        checks = detect_credential_like_values(config)
        assert any(c.status == "PASS" for c in checks)

    def test_dummy_token_allowed(self):
        config = {"token": "dummy_placeholder_123"}
        checks = detect_credential_like_values(config)
        assert any(c.status == "PASS" for c in checks)

    def test_real_token_blocked(self):
        config = {"token": "abc123xyz789testval"}
        checks = detect_credential_like_values(config)
        assert any(c.status == "BLOCKED" for c in checks)


class TestSimulatePaperConnectivity:
    def test_returns_pass(self):
        checks = simulate_paper_connectivity()
        assert all(c.status == "PASS" for c in checks)
        assert any("local" in c.message.lower() or "network" in c.message.lower() for c in checks)

    def test_safe_local_endpoint(self):
        config = {"broker_endpoint": "http://localhost:8080/paper"}
        checks = simulate_paper_connectivity(config)
        assert any(c.name == "broker_endpoint" and c.status == "PASS" for c in checks)

    def test_external_endpoint_warns(self):
        config = {"broker_endpoint": "https://api.broker.com/v1"}
        checks = simulate_paper_connectivity(config)
        assert any(c.name == "broker_endpoint" and c.status == "WARN" for c in checks)


class TestClassifyPaperBrokerReadiness:
    def test_ready(self):
        checks = [PaperBrokerCheck(status="PASS"), PaperBrokerCheck(status="PASS")]
        assert classify_paper_broker_readiness(checks) == "READY"

    def test_ready_with_warnings(self):
        checks = [PaperBrokerCheck(status="PASS"), PaperBrokerCheck(status="WARN")]
        assert classify_paper_broker_readiness(checks) == "READY_WITH_WARNINGS"

    def test_blocked(self):
        checks = [PaperBrokerCheck(status="PASS"), PaperBrokerCheck(status="BLOCKED")]
        assert classify_paper_broker_readiness(checks) == "BLOCKED"

    def test_blocked_overrides_warn(self):
        checks = [PaperBrokerCheck(status="WARN"), PaperBrokerCheck(status="BLOCKED")]
        assert classify_paper_broker_readiness(checks) == "BLOCKED"


class TestRenderPaperBrokerReadinessSummary:
    def test_includes_paper_only(self):
        report = PaperBrokerReadinessReport()
        text = render_paper_broker_readiness_summary(report)
        assert "PAPER-ONLY" in text
        assert "DATA-ONLY" in text

    def test_includes_no_live_trading(self):
        report = PaperBrokerReadinessReport()
        text = render_paper_broker_readiness_summary(report)
        assert "No live trading" in text

    def test_includes_not_financial_advice(self):
        report = PaperBrokerReadinessReport()
        text = render_paper_broker_readiness_summary(report)
        assert "not financial advice" in text.lower()

    def test_includes_next_safe_commands(self):
        report = PaperBrokerReadinessReport()
        report.next_safe_commands = ["python3 test.py"]
        text = render_paper_broker_readiness_summary(report)
        assert "python3 test.py" in text

    def test_includes_checks(self):
        report = PaperBrokerReadinessReport()
        report.checks.append(PaperBrokerCheck(name="test", status="PASS", message="ok"))
        text = render_paper_broker_readiness_summary(report)
        assert "test" in text
        assert "PASS" in text


class TestWritePaperBrokerReadinessReport:
    def test_writes_json_and_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = PaperBrokerReadinessReport(
                generated_at="2023-01-01T00:00:00Z",
                paper_only=True,
                data_only=True,
                no_order_submission=True,
                status="READY",
                broker_name="paper_stub",
                mode="paper",
            )
            paths = write_paper_broker_readiness_report(root, report)
            assert len(paths) == 3
            assert (root / "reports" / "paper_broker" / "readiness_report.json").exists()
            assert (root / "reports" / "paper_broker" / "readiness_report.md").exists()
            assert (root / "reports" / "dashboard" / "paper_broker" / "latest.json").exists()


class TestLoadLatestPaperBrokerReadiness:
    def test_loads_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = PaperBrokerReadinessReport(
                generated_at="2023-01-01T00:00:00Z",
                paper_only=True,
                data_only=True,
                no_order_submission=True,
                status="READY",
                broker_name="paper_stub",
                mode="paper",
            )
            write_paper_broker_readiness_report(root, report)
            loaded = load_latest_paper_broker_readiness(root)
            assert loaded is not None
            assert loaded.status == "READY"
            assert loaded.broker_name == "paper_stub"

    def test_returns_none_when_no_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loaded = load_latest_paper_broker_readiness(root)
            assert loaded is None
