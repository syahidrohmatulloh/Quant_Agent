"""Tests for ImportLog."""
import json
import tempfile
from pathlib import Path

from data_manager.import_log import ImportLog


def test_import_log_writes_append_only_jsonl():
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "log.jsonl"
        log = ImportLog(log_path)
        log.append("id1", "cfg", "mt5", "EURUSD", "H1",
                   "raw.csv", "target.csv", "upsert", 10, 9, 1, 95)
        log.append("id2", "cfg", "mt5", "GBPUSD", "H1",
                   "raw.csv", "target.csv", "upsert", 10, 10, 0, 98)
        with open(log_path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2
        for line in lines:
            rec = json.loads(line)
            assert rec["paper_only"] is True
            assert rec["data_only"] is True
            assert rec["no_order_submission"] is True
