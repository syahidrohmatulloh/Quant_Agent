"""Append-only JSONL logging for trades and PnL.

Never include credentials. Never include env vars. Never include broker secrets.
"""
import json
from pathlib import Path
from typing import Dict, Any


def append_trade_log(record: Dict[str, Any], log_path: str) -> None:
    """Append a trade fill record to JSONL."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + chr(10))


def append_pnl_log(record: Dict[str, Any], log_path: str) -> None:
    """Append a PnL snapshot record to JSONL."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + chr(10))
