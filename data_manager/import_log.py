"""ImportLog - append-only JSONL import log."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class ImportLog:
    """Append-only JSONL log for data imports."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, import_id: str, config_name: str, source: str,
               symbol: str, timeframe: str, raw_csv: str, target_csv: str,
               mode: str, rows_in: int, rows_out: int, rows_dropped: int,
               quality_score: int, backup_path: Optional[str] = None) -> Dict[str, Any]:
        record = {
            "import_id": import_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config_name": config_name,
            "source": source,
            "symbol": symbol,
            "timeframe": timeframe,
            "raw_csv": raw_csv,
            "target_csv": target_csv,
            "mode": mode,
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rows_dropped": rows_dropped,
            "quality_score": quality_score,
            "backup_path": backup_path,
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record
