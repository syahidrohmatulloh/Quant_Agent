"""
Append-only experiment history log (JSONL).
Paper-only. No live trading.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def append_experiment_log(history_dir, run_id, experiment_name, config_path, symbol_count, strategy_count, result_path, dashboard_json_path):
    hist_dir = Path(history_dir)
    hist_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(Path(config_path).resolve()),
        "experiment_name": experiment_name,
        "symbol_count": symbol_count,
        "strategy_count": strategy_count,
        "paper_only": True,
        "data_only": True,
        "result_path": str(Path(result_path).resolve()),
        "dashboard_json_path": str(Path(dashboard_json_path).resolve()),
        "no_order_submission": True,
    }

    history_file = hist_dir / "experiment_history.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

    return str(history_file)


def list_experiment_history(history_dir):
    hist_file = Path(history_dir) / "experiment_history.jsonl"
    if not hist_file.exists():
        return []
    records = []
    with open(hist_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records
