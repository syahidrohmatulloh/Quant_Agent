import os
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


class AuditLogger:
    """Append-only hash-chained audit log that resumes across process restarts."""

    def __init__(self, path: str = "./data/audit.jsonl"):
        self.path = path
        self._sequence = 0
        self._last_hash = "GENESIS"

        parent = Path(path).expanduser().parent
        if str(parent):
            parent.mkdir(parents=True, exist_ok=True)
        self._resume_chain()

    def _resume_chain(self) -> None:
        p = Path(self.path)
        if not p.exists() or p.stat().st_size == 0:
            return

        last_record = None
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                last_record = json.loads(line)

        if last_record is None:
            return

        sequence = last_record.get("event_sequence")
        event_hash = last_record.get("event_hash")
        if not isinstance(sequence, int) or sequence < 1 or not event_hash:
            raise ValueError("Existing audit log has an invalid final record")

        self._sequence = sequence
        self._last_hash = str(event_hash)

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def log(
        self,
        event_type: str,
        request_id: str,
        actor: str,
        role: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._sequence += 1
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = self._hash(payload_json)
        prev_hash = self._last_hash
        event_hash = self._hash(
            f"{self._sequence}{event_id}{event_type}{request_id}{actor}{role}"
            f"{payload_hash}{prev_hash}{timestamp}"
        )
        record = {
            "event_sequence": self._sequence,
            "event_id": event_id,
            "event_type": event_type,
            "request_id": request_id,
            "actor": actor,
            "role": role,
            "payload_json": payload_json,
            "payload_hash": payload_hash,
            "previous_event_hash": prev_hash,
            "event_hash": event_hash,
            "timestamp_utc": timestamp,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
        self._last_hash = event_hash
        return record
