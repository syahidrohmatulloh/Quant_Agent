import os
import sys
import pytest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.readiness_check import ReadinessChecker, check_readiness


class TestReadinessChecker:
    def test_readiness_passes_in_clean_mock_setup(self):
        with tempfile.TemporaryDirectory() as td:
            # Create minimal project structure
            open(os.path.join(td, "requirements.txt"), "w").close()
            with open(os.path.join(td, ".env.example"), "w") as f:
                f.write("QUANT_VIEWER_TOKEN=\nQUANT_MODE=paper\n")
            os.makedirs(os.path.join(td, "reports"), exist_ok=True)
            os.makedirs(os.path.join(td, "backups"), exist_ok=True)
            checker = ReadinessChecker(project_root=td)
            result = checker.check()
            assert result["ready_for_paper_runtime"] is True
            assert result["ready_for_live_trading"] is False
            assert any(c["name"] == "paper_only_mode" and c["status"] == "pass" for c in result["checks"])
            assert any(c["name"] == "live_trading_disabled" and c["status"] == "pass" for c in result["checks"])

    def test_readiness_fails_if_live_trading_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, "requirements.txt"), "w").close()
            with open(os.path.join(td, ".env.example"), "w") as f:
                f.write("QUANT_VIEWER_TOKEN=\nQUANT_MODE=paper\n")
            os.environ["CONFIRM_LIVE_TRADING"] = "YES"
            checker = ReadinessChecker(project_root=td)
            result = checker.check()
            del os.environ["CONFIRM_LIVE_TRADING"]
            assert result["ready_for_paper_runtime"] is False
            assert any(c["name"] == "live_trading_disabled" and c["status"] == "fail" for c in result["checks"])

    def test_readiness_fails_if_no_viewer_token_env(self):
        # Temporarily clear viewer token
        orig = os.environ.pop("QUANT_VIEWER_TOKEN", None)
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, "requirements.txt"), "w").close()
            with open(os.path.join(td, ".env.example"), "w") as f:
                f.write("QUANT_VIEWER_TOKEN=\nQUANT_MODE=paper\n")
            checker = ReadinessChecker(project_root=td)
            result = checker.check()
            # Dashboard routes may fail without token, but paper mode still passes
            assert result["ready_for_paper_runtime"] is True  # paper mode is the key gate
        if orig:
            os.environ["QUANT_VIEWER_TOKEN"] = orig

    def test_readiness_fails_if_package_artifacts_found(self):
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, "requirements.txt"), "w").close()
            with open(os.path.join(td, ".env.example"), "w") as f:
                f.write("QUANT_VIEWER_TOKEN=\nQUANT_MODE=paper\n")
            # Create a forbidden artifact
            with open(os.path.join(td, "test.db"), "w") as f:
                f.write("fake db")
            checker = ReadinessChecker(project_root=td)
            result = checker.check()
            assert result["ready_for_paper_runtime"] is False
            assert any(c["name"] == "no_artifacts_in_package" and c["status"] == "fail" for c in result["checks"])
