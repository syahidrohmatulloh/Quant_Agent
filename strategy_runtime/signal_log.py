"""
Append-only signal log for paper-only CSV workflow.
No live trading. No order submission.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


def _ensure_dir(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def log_signal(
    signal: Dict[str, Any],
    log_path: str = "reports/signals/signal_log.jsonl",
) -> None:
    """Append a single signal record to JSONL log."""
    p = _ensure_dir(log_path)
    record = {
        "created_at": datetime.now().isoformat(),
        "symbol": signal.get("symbol", "UNKNOWN"),
        "timeframe": signal.get("timeframe", "UNKNOWN"),
        "strategy": signal.get("strategy", "UNKNOWN"),
        "signal_direction": signal.get("direction", "hold"),
        "score": signal.get("score"),
        "weight": signal.get("weight"),
        "confidence": signal.get("confidence"),
        "source_csv": signal.get("source_csv", ""),
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
    }
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_signals(log_path: str = "reports/signals/signal_log.jsonl") -> list:
    """Read all signals from JSONL log."""
    p = Path(log_path)
    if not p.exists():
        return []
    signals = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            signals.append(json.loads(line))
    return signals
