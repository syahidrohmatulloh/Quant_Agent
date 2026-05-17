"""
Data quality result structures and helpers.
Data-only. No live trading.
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataQualityReport:
    valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    row_count: int = 0
    first_timestamp: str = ""
    last_timestamp: str = ""
    inferred_symbol: str = "UNKNOWN"
    inferred_timeframe: str = "UNKNOWN"
    inferred_source: str = "UNKNOWN"
    duplicate_count: int = 0
    detected_gaps: int = 0
    price_anomaly_count: int = 0
    bad_price_count: int = 0
    future_timestamp_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "row_count": self.row_count,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "inferred_symbol": self.inferred_symbol,
            "inferred_timeframe": self.inferred_timeframe,
            "inferred_source": self.inferred_source,
            "duplicate_count": self.duplicate_count,
            "detected_gaps": self.detected_gaps,
            "price_anomaly_count": self.price_anomaly_count,
            "bad_price_count": self.bad_price_count,
            "future_timestamp_count": self.future_timestamp_count,
        }


def build_quality_report(validation_result: Dict[str, Any]) -> DataQualityReport:
    """Convert raw validation dict to typed report."""
    return DataQualityReport(
        valid=validation_result.get("valid", False),
        errors=validation_result.get("errors", []),
        warnings=validation_result.get("warnings", []),
        row_count=validation_result.get("row_count", 0),
        first_timestamp=validation_result.get("first_timestamp", ""),
        last_timestamp=validation_result.get("last_timestamp", ""),
        inferred_symbol=validation_result.get("inferred_symbol", "UNKNOWN"),
        inferred_timeframe=validation_result.get("inferred_timeframe", "UNKNOWN"),
        inferred_source=validation_result.get("inferred_source", "UNKNOWN"),
        duplicate_count=validation_result.get("duplicate_count", 0),
        detected_gaps=validation_result.get("gap_count", 0),
        price_anomaly_count=validation_result.get("price_anomaly_count", 0),
        bad_price_count=validation_result.get("bad_price_count", 0),
        future_timestamp_count=validation_result.get("future_timestamp_count", 0),
    )
