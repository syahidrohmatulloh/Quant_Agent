"""CatalogRefresh - updates dataset catalog JSON."""
import json
from pathlib import Path
from typing import Any, Dict

from .quality_score import ScoreResult


class CatalogRefresh:
    """Refreshes dataset catalog after imports."""

    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = Path(catalog_path)
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

    def refresh(self, dataset_path: Path, symbol: str, timeframe: str,
                source: str, quality: ScoreResult) -> Dict[str, Any]:
        from datetime import datetime, timezone
        catalog = self._load_catalog()
        entry = {
            "symbol": symbol,
            "timeframe": timeframe,
            "source": source,
            "path": str(dataset_path),
            "row_count": quality.metrics.get("row_count", 0),
            "first_timestamp": quality.metrics.get("first_timestamp", ""),
            "last_timestamp": quality.metrics.get("last_timestamp", ""),
            "quality_score": quality.score,
            "last_imported_at": datetime.now(timezone.utc).isoformat(),
        }
        catalog["datasets"] = [
            d for d in catalog.get("datasets", [])
            if d.get("path") != str(dataset_path)
        ]
        catalog["datasets"].append(entry)
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        return entry

    def _load_catalog(self) -> Dict[str, Any]:
        if self.catalog_path.exists():
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"datasets": []}
