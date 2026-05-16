"""Runtime health checks for scheduler, data adapters, and core services."""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from scheduler.heartbeat import Heartbeat
from live_data.csv_replay_adapter import CSVReplayAdapter
from storage.db import SQLiteStore
from storage.audit import AuditLogger


class RuntimeHealthChecker:
    """Checks runtime health of all critical components."""

    def __init__(self,
                 db_path: str = "./data/quant_platform.db",
                 audit_path: str = "./data/audit.jsonl",
                 heartbeat_max_age: float = 60.0):
        self.db_path = db_path
        self.audit_path = audit_path
        self.heartbeat_max_age = heartbeat_max_age
        self.checks: List[Dict[str, Any]] = []

    def check(self) -> Dict[str, Any]:
        self.checks = []
        # 1. SQLite connectivity
        self._check_sqlite()
        # 2. Audit log writable
        self._check_audit()
        # 3. Heartbeat freshness
        self._check_heartbeat()
        # 4. Data directory writable
        self._check_data_dir()
        # 5. Paper mode confirmed
        self._check_paper_mode()
        all_ok = all(c["status"] == "ok" for c in self.checks)
        return {
            "healthy": all_ok,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "checks": self.checks
        }

    def _check_sqlite(self):
        try:
            store = SQLiteStore(self.db_path)
            self.checks.append({"component": "sqlite", "status": "ok", "path": self.db_path})
        except Exception as e:
            self.checks.append({"component": "sqlite", "status": "error", "error": str(e)})

    def _check_audit(self):
        try:
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
            dir_path = os.path.dirname(self.db_path) or "."
            test_file = os.path.join(dir_path, ".write_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            self.checks.append({"component": "data_dir", "status": "ok", "path": dir_path})
        except Exception as e:
            self.checks.append({"component": "data_dir", "status": "error", "error": str(e)})

    def _check_paper_mode(self):
        mode = os.getenv("QUANT_MODE", "paper")
        broker = os.getenv("QUANT_BROKER", "paper")
        if mode == "paper" and broker == "paper":
            self.checks.append({"component": "paper_mode", "status": "ok", "mode": mode, "broker": broker})
        else:
            self.checks.append({"component": "paper_mode", "status": "warning", "mode": mode, "broker": broker})
