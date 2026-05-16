from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if any(s in lk for s in ("key", "secret", "token", "password", "credential")):
                clean[k] = "***REDACTED***"
            else:
                clean[k] = _redact(v)
        return clean
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


class StreamRecorder:
    def __init__(self, output_root: str, session_id: str = "stream-session"):
        self.output_root = output_root
        self.session_id = session_id
        self.output_dir = os.path.join(output_root, session_id)
        os.makedirs(self.output_dir, exist_ok=True)

        self._ticks: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        self._errors: List[Dict[str, Any]] = []

    def record_tick(self, tick: Dict[str, Any]) -> None:
        self._ticks.append(_redact(dict(tick)))

    def record_event(self, event: Any) -> None:
        if hasattr(event, "to_dict"):
            payload = event.to_dict()
        elif hasattr(event, "__dict__"):
            payload = dict(event.__dict__)
        elif isinstance(event, dict):
            payload = dict(event)
        else:
            payload = {"event": str(event)}
        self._events.append(_redact(payload))

    def record_error(self, error: Any) -> None:
        if isinstance(error, dict):
            payload = dict(error)
        else:
            payload = {"error": str(error)}
        self._errors.append(_redact(payload))

    def _write_jsonl(self, path: str, rows: List[Dict[str, Any]]) -> None:
        with open(path, "w") as f:
            for item in rows:
                f.write(json.dumps(_redact(item), default=str) + "\n")

    def _write_ticks_csv(self, path: str) -> None:
        preferred = ["symbol", "timestamp_utc", "bid", "ask", "mid", "spread", "volume", "source"]
        fields = list(preferred)

        for row in self._ticks:
            for key in row.keys():
                if key not in fields:
                    fields.append(key)

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in self._ticks:
                writer.writerow({k: row.get(k, "") for k in fields})

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "ticks_count": len(self._ticks),
            "events_count": len(self._events),
            "errors_count": len(self._errors),
            "paper_only": True,
        }

    def flush(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        self._write_ticks_csv(os.path.join(self.output_dir, "ticks.csv"))
        self._write_jsonl(os.path.join(self.output_dir, "events.jsonl"), self._events)
        self._write_jsonl(os.path.join(self.output_dir, "errors.jsonl"), self._errors)

        with open(os.path.join(self.output_dir, "summary.json"), "w") as f:
            json.dump(self.summary(), f, indent=2, default=str)
