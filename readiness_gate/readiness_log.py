"""Append-only readiness log (JSONL).

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from .readiness_score import ReadinessScore


class ReadinessLog:
    def __init__(self) -> None:
        self.record: Dict[str, Any] = {}


def append_readiness_log(
    path: Path,
    score: ReadinessScore,
    critical_count: int,
    warning_count: int,
) -> ReadinessLog:
    log = ReadinessLog()
    now = datetime.now(timezone.utc).isoformat()
    log.record = {
        "readiness_id": str(uuid.uuid4()),
        "generated_at": now,
        "score": score.score,
        "grade": score.grade,
        "readiness_status": score.status,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log.record) + "\n")
    return log
