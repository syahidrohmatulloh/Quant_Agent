import os
import sys
import pytest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.runtime_health import RuntimeHealthChecker


class TestRuntimeHealthChecker:
    def test_health_check_passes_in_clean_setup(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "test.db")
            audit_path = os.path.join(td, "audit.jsonl")
            checker = RuntimeHealthChecker(db_path=db_path, audit_path=audit_path)
            result = checker.check()
            assert result["healthy"] is True
            assert any(c["component"] == "sqlite" and c["status"] == "ok" for c in result["checks"])
            assert any(c["component"] == "audit" and c["status"] == "ok" for c in result["checks"])
            assert any(c["component"] == "heartbeat" and c["status"] == "ok" for c in result["checks"])
            assert any(c["component"] == "paper_mode" and c["status"] == "ok" for c in result["checks"])

    def test_health_fails_if_db_not_writable(self):
        # On most systems we can test with a read-only path conceptually
        # Here we just verify the checker reports error for bad path
        checker = RuntimeHealthChecker(db_path="/nonexistent/path/test.db", audit_path="/nonexistent/audit.jsonl")
        result = checker.check()
        assert result["healthy"] is False
        assert any(c["component"] == "sqlite" and c["status"] == "error" for c in result["checks"])
