"""Runtime health checks for scheduler, data adapters, and core services."""
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

from scheduler.heartbeat import Heartbeat
from storage.db import SQLiteStore
from storage.audit import AuditLogger


class RuntimeHealthChecker:
    """Checks runtime health of all critical components without creating missing parent dirs."""

    def __init__(
        self,
        db_path: str = "./data/quant_platform.db",
        audit_path: str = "./data/audit.jsonl",
        heartbeat_max_age: float = 60.0,
    ):
        self.db_path = db_path
        self.audit_path = audit_path
        self.heartbeat_max_age = heartbeat_max_age
        self.checks: List[Dict[str, Any]] = []

    def check(self) -> Dict[str, Any]:
        self.checks = []
        self._check_sqlite()
        self._check_audit()
        self._check_heartbeat()
        self._check_data_dir()
        self._check_paper_mode()
        all_ok = all(c["status"] == "ok" for c in self.checks)
        return {
            "healthy": all_ok,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "checks": self.checks,
        }

    @staticmethod
    def _existing_parent(path: str) -> Path:
        parent = Path(path).expanduser().parent
        if not parent.exists() or not parent.is_dir():
            raise FileNotFoundError(f"Parent directory does not exist: {parent}")
        if not os.access(parent, os.W_OK):
            raise PermissionError(f"Parent directory is not writable: {parent}")
        return parent

    def _check_sqlite(self):
        try:
            self._existing_parent(self.db_path)
            SQLiteStore(self.db_path)
            self.checks.append({"component": "sqlite", "status": "ok", "path": self.db_path})
        except Exception as e:
            self.checks.append({"component": "sqlite", "status": "error", "error": str(e)})

    def _check_audit(self):
        try:
            self._existing_parent(self.audit_path)
            audit = AuditLogger(self.audit_path)
            audit.log("health_check", "health-1", "system", "system", {"check": "audit_writable"})
            self.checks.append({"component": "audit", "status": "ok", "path": self.audit_path})
        except Exception as e:
            self.checks.append({"component": "audit", "status": "error", "error": str(e)})

    def _check_heartbeat(self):
        try:
            hb = Heartbeat(component="runtime_health")
            hb.beat(status="ok")
            if hb.is_stale(max_age_seconds=self.heartbeat_max_age):
                self.checks.append({"component": "heartbeat", "status": "stale"})
            else:
                self.checks.append({"component": "heartbeat", "status": "ok"})
        except Exception as e:
            self.checks.append({"component": "heartbeat", "status": "error", "error": str(e)})

    def _check_data_dir(self):
        try:
            dir_path = self._existing_parent(self.db_path)
            test_file = dir_path / ".write_test"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("ok")
            test_file.unlink()
            self.checks.append({"component": "data_dir", "status": "ok", "path": str(dir_path)})
        except Exception as e:
            self.checks.append({"component": "data_dir", "status": "error", "error": str(e)})

    def _check_paper_mode(self):
        mode = os.getenv("QUANT_MODE", "paper").lower()
        broker = os.getenv("QUANT_BROKER", "paper").lower()
        if mode == "paper" and broker == "paper":
            self.checks.append({"component": "paper_mode", "status": "ok", "mode": mode, "broker": broker})
        else:
            self.checks.append({"component": "paper_mode", "status": "error", "mode": mode, "broker": broker})
