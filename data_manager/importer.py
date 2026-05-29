"""Importer - orchestrates import, normalize, clean, merge, score, log, catalog."""
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .import_config import ImportConfig
from .schema_detector import SchemaDetector
from .normalizer import Normalizer, CANONICAL_COLUMNS
from .cleaner import Cleaner, CleanResult
from .merger import Merger, MergeResult
from .versioning import Versioning
from .quality_score import QualityScore, ScoreResult
from .catalog_refresh import CatalogRefresh
from .import_log import ImportLog


@dataclass
class ImportResult:
    config_name: str = ""
    dataset_results: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Importer:
    """Orchestrates full import workflow for one config."""

    def __init__(self, config: ImportConfig) -> None:
        self.config = config
        self.detector = SchemaDetector()
        self.normalizer = Normalizer()
        self.cleaner = Cleaner()
        self.merger = Merger()
        self.versioning = Versioning(Path(config.get("backup_dir", "data/market_versions")))
        self.quality = QualityScore()
        self.catalog = CatalogRefresh(Path(config.get("catalog_path",
                                                      "reports/data_manager/dataset_catalog.json")))
        self.log = ImportLog(Path(config.get("import_log_path",
                                             "reports/data_manager/import_log.jsonl")))

    def run(self) -> ImportResult:
        result = ImportResult(config_name=self.config.name)
        if not self.config.is_valid:
            result.errors.extend(self.config.errors)
            return result
        datasets = self.config.raw.get("datasets", [])
        cleaning = self.config.raw.get("cleaning", {})
        merge_cfg = self.config.raw.get("merge", {})
        quality_cfg = self.config.raw.get("quality", {})
        for ds in datasets:
            raw_csv = Path(ds["raw_csv"])
            target_csv = Path(ds["target_csv"])
            symbol = ds["symbol"]
            timeframe = ds["timeframe"]
            source_name = ds["source"]
            try:
                schema = self.detector.detect(raw_csv)
                norm_path = self.normalizer.normalize(
                    raw_csv, schema, symbol, timeframe, source_name
                )
                clean_result = self.cleaner.clean(
                    norm_path,
                    remove_duplicates=cleaning.get("remove_duplicate_timestamps", True),
                    sort_by_timestamp=cleaning.get("sort_by_timestamp", True),
                    drop_malformed=cleaning.get("drop_malformed_rows", True),
                    drop_non_positive_prices=cleaning.get("drop_non_positive_prices", True),
                    fix_column_aliases=cleaning.get("fix_column_aliases", True),
                )
                backup_path: Optional[str] = None
                if target_csv.exists() and merge_cfg.get("backup_before_write", True):
                    bp = self.versioning.backup(target_csv)
                    backup_path = str(bp)
                merge_result = self.merger.merge(
                    clean_result.rows_out > 0 and norm_path or raw_csv,
                    target_csv,
                    mode=merge_cfg.get("mode", "upsert_by_timestamp"),
                    backup_before_write=False,
                    preserve_existing_if_new_invalid=merge_cfg.get(
                        "preserve_existing_if_new_invalid", True
                    ),
                )
                if merge_result.preserved_existing:
                    result.warnings.append(
                        "Preserved existing " + str(target_csv) + " because new data invalid"
                    )
                score = self.quality.score(
                    target_csv, symbol, timeframe,
                    minimum_rows=quality_cfg.get("minimum_rows", 20),
                    warn_on_gaps=quality_cfg.get("warn_on_gaps", True),
                    warn_on_future_timestamps=quality_cfg.get("warn_on_future_timestamps", True),
                )
                self.catalog.refresh(target_csv, symbol, timeframe, source_name, score)
                import_id = str(uuid.uuid4())[:8]
                self.log.append(
                    import_id=import_id,
                    config_name=self.config.name,
                    source=source_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    raw_csv=str(raw_csv),
                    target_csv=str(target_csv),
                    mode=merge_cfg.get("mode", "upsert_by_timestamp"),
                    rows_in=clean_result.rows_in,
                    rows_out=clean_result.rows_out,
                    rows_dropped=clean_result.rows_dropped,
                    quality_score=score.score,
                    backup_path=backup_path,
                )
                result.dataset_results.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "target_csv": str(target_csv),
                    "rows_in": clean_result.rows_in,
                    "rows_out": clean_result.rows_out,
                    "rows_dropped": clean_result.rows_dropped,
                    "quality_score": score.score,
                    "grade": score.grade,
                    "backup_path": backup_path,
                })
            except Exception as e:
                result.errors.append("Dataset " + symbol + "/" + timeframe + ": " + str(e))
        return result
