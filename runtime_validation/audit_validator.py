"""Audit runtime validation: chain integrity, completeness, no live execution events."""
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class AuditRuntimeValidator:
    """Validates audit trail integrity and completeness at runtime."""

    def __init__(self, audit_path: str = "./data/audit.jsonl", db_path: str = "./data/quant_platform.db"):
        self.audit_path = audit_path
        self.db_path = db_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Dict[str, Any]:
        self.errors = []
        self.warnings = []
        if not os.path.exists(self.audit_path):
            return {"valid": False, "errors": ["Audit file not found"], "warnings": [], "events_checked": 0}

        events = self._load_events()
        if not events:
            return {"valid": False, "errors": ["No audit events found"], "warnings": [], "events_checked": 0}

        self._validate_chain(events)
        self._validate_completeness(events)
        self._validate_no_live_execution(events)
        self._validate_timestamps(events)

        valid = len(self.errors) == 0
        return {
            "valid": valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "events_checked": len(events),
            "first_event": events[0].get("event_id"),
            "last_event": events[-1].get("event_id"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }

    def _load_events(self) -> List[Dict[str, Any]]:
        events = []
        with open(self.audit_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    self.errors.append("Invalid JSON line in audit file")
        return events

    def _validate_chain(self, events: List[Dict[str, Any]]):
        for i, ev in enumerate(events):
            if i == 0:
                if ev.get("previous_event_hash") != "GENESIS":
                    self.errors.append(f"First event {ev.get('event_id')} does not chain from GENESIS")
                continue
            prev = events[i - 1]
            expected_prev_hash = prev.get("event_hash")
            actual_prev_hash = ev.get("previous_event_hash")
            if actual_prev_hash != expected_prev_hash:
                self.errors.append(f"Broken chain at event {ev.get('event_id')}: expected prev_hash {expected_prev_hash}, got {actual_prev_hash}")
            # Recompute hash
            payload_hash = ev.get("payload_hash", "")
            prev_hash = ev.get("previous_event_hash", "")
            recompute_full = hashlib.sha256(
                f"{ev.get('event_sequence')}{ev.get('event_id')}{ev.get('event_type')}{ev.get('request_id')}{ev.get('actor')}{ev.get('role')}{payload_hash}{prev_hash}{ev.get('timestamp_utc')}".encode()
            ).hexdigest()
            stored_hash = str(ev.get("event_hash", ""))
            # Accept legacy 16-char hashes and current full SHA-256 hashes.
            if not stored_hash or recompute_full[:len(stored_hash)] != stored_hash:
                self.errors.append(f"Hash mismatch at event {ev.get('event_id')}")

    def _validate_completeness(self, events: List[Dict[str, Any]]):
        signal_events = [e for e in events if e.get("event_type") == "signal_generated"]
        for se in signal_events:
            req_id = se.get("request_id")
            # Check for corresponding paper_order_created or signal_rejected
            related = [e for e in events if e.get("request_id") == req_id and e.get("event_type") in ("paper_order_created", "signal_rejected")]
            if not related:
                self.errors.append(f"Signal {req_id} has no follow-up order or rejection event")

        # Check every rejection has a reason
        rejections = [e for e in events if e.get("event_type") == "signal_rejected"]
        for r in rejections:
            payload = json.loads(r.get("payload_json", "{}"))
            if not payload.get("reason"):
                self.errors.append(f"Rejection event {r.get('event_id')} missing reason")

    def _validate_no_live_execution(self, events: List[Dict[str, Any]]):
        live_types = {"live_order_created", "live_order_executed", "live_position_opened", "broker_live_order"}
        for e in events:
            if e.get("event_type") in live_types:
                self.errors.append(f"Live execution event found: {e.get('event_id')} type={e.get('event_type')}")

    def _validate_timestamps(self, events: List[Dict[str, Any]]):
        prev_ts = None
        for e in events:
            ts_str = e.get("timestamp_utc")
            if not ts_str:
                self.warnings.append(f"Event {e.get('event_id')} missing timestamp")
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if prev_ts and ts < prev_ts:
                    self.errors.append(f"Timestamp gap/backwards at event {e.get('event_id')}")
                prev_ts = ts
            except Exception:
                self.warnings.append(f"Event {e.get('event_id')} has unparsable timestamp")
