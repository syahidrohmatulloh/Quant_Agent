from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _redact_record(record: Any) -> Any:
    if isinstance(record, str):
        return record

    if not isinstance(record, dict):
        return record

    secret_markers = ("key", "secret", "token", "password", "credential")
    clean: Dict[str, Any] = {}

    for k, v in record.items():
        if any(marker in str(k).lower() for marker in secret_markers):
            clean[k] = "***REDACTED***"
        else:
            clean[k] = v

    return clean


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)


def _write_dynamic_csv(path: str, rows: List[Dict[str, Any]], preferred_fields: List[str] | None = None) -> None:
    rows = [_redact_record(dict(r)) for r in rows]
    fields = list(preferred_fields or [])

    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


class RuntimeRecorder:
    def __init__(self, output_root: str, session_id: str):
        self.output_root = output_root
        self.session_id = session_id
        self.output_dir = os.path.join(output_root, session_id)
        os.makedirs(self.output_dir, exist_ok=True)

        self._ticks: List[Dict[str, Any]] = []
        self._signals: List[Dict[str, Any]] = []
        self._rejections: List[Dict[str, Any]] = []
        self._snapshots: List[Dict[str, Any]] = []
        self._reconciliations: List[Dict[str, Any]] = []
        self._alerts: List[Any] = []

    def record_tick(self, tick: Dict[str, Any]) -> None:
        self._ticks.append(_redact_record(dict(tick)))

    def record_signal(self, signal: Dict[str, Any]) -> None:
        self._signals.append(_redact_record(dict(signal)))

    def record_rejection(self, rejection: Dict[str, Any]) -> None:
        self._rejections.append(_redact_record(dict(rejection)))

    def record_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self._snapshots.append(_redact_record(dict(snapshot)))

    def record_reconciliation(self, reconciliation: Dict[str, Any]) -> None:
        self._reconciliations.append(_redact_record(dict(reconciliation)))

    def record_alert(self, alert: Any) -> None:
        if isinstance(alert, dict):
            self._alerts.append(_redact_record(dict(alert)))
        else:
            self._alerts.append(str(alert))

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "ticks_count": len(self._ticks),
            "signals_count": len(self._signals),
            "rejections_count": len(self._rejections),
            "snapshots_count": len(self._snapshots),
            "reconciliations_count": len(self._reconciliations),
            "alerts_count": len(self._alerts),
            "paper_only": True,
        }

    def flush(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)

        _write_dynamic_csv(
            os.path.join(self.output_dir, "ticks.csv"),
            self._ticks,
            ["symbol", "timestamp_utc", "bid", "ask", "mid", "spread", "volume", "source"],
        )

        _write_dynamic_csv(
            os.path.join(self.output_dir, "signals.csv"),
            self._signals,
            ["symbol", "direction", "signal", "confidence", "timestamp_utc"],
        )
        _write_dynamic_csv(
            os.path.join(self.output_dir, "rejections.csv"),
            self._rejections,
            ["reason", "symbol", "timestamp_utc"],
        )

        _write_json(os.path.join(self.output_dir, "signals.json"), self._signals)
        _write_json(os.path.join(self.output_dir, "rejections.json"), self._rejections)
        _write_json(os.path.join(self.output_dir, "snapshots.json"), self._snapshots)
        _write_json(os.path.join(self.output_dir, "reconciliation.json"), self._reconciliations)
        _write_json(os.path.join(self.output_dir, "alerts.json"), self._alerts)
        _write_json(os.path.join(self.output_dir, "summary.json"), self.summary())
        _write_json(os.path.join(self.output_dir, "session_summary.json"), self.summary())
