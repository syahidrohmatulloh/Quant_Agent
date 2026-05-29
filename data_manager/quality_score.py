"""QualityScore - scores dataset quality 0-100 with A/B/C/D/F grade."""
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ScoreResult:
    score: int = 0
    grade: str = "F"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class QualityScore:
    """Scores a canonical market dataset."""

    def score(self, csv_path: Path, symbol: str, timeframe: str,
              minimum_rows: int = 20,
              warn_on_gaps: bool = True,
              warn_on_future_timestamps: bool = True) -> ScoreResult:
        result = ScoreResult()
        if not csv_path.exists():
            result.errors.append("File not found: " + str(csv_path))
            result.score = 0
            result.grade = "F"
            return result
        rows: List[Dict[str, Any]] = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        total = len(rows)
        result.metrics["row_count"] = total
        if total < minimum_rows:
            result.warnings.append("Row count " + str(total) + " below minimum " + str(minimum_rows))
        headers = list(rows[0].keys()) if rows else []
        canonical = ["timestamp", "open", "high", "low", "close"]
        missing = [c for c in canonical if c not in headers]
        result.metrics["missing_canonical"] = missing
        if missing:
            result.errors.append("Missing canonical columns: " + str(missing))
        timestamps = [r.get("timestamp", "") for r in rows if r.get("timestamp")]
        duplicates = total - len(set(timestamps))
        result.metrics["duplicate_timestamps"] = duplicates
        if duplicates:
            result.warnings.append("Duplicate timestamps: " + str(duplicates))
        malformed = 0
        anomalies = 0
        for r in rows:
            for key in ("open", "high", "low", "close"):
                val = r.get(key, "").strip()
                if val == "":
                    malformed += 1
                    break
                try:
                    fval = float(val)
                    if fval <= 0:
                        anomalies += 1
                except ValueError:
                    malformed += 1
                    break
        result.metrics["malformed_rows"] = malformed
        result.metrics["price_anomalies"] = anomalies
        if malformed:
            result.warnings.append("Malformed rows: " + str(malformed))
        if anomalies:
            result.warnings.append("Price anomalies: " + str(anomalies))
        non_mono = 0
        if warn_on_gaps and len(timestamps) > 1:
            sorted_ts = sorted(timestamps)
            result.metrics["first_timestamp"] = sorted_ts[0] if sorted_ts else ""
            result.metrics["last_timestamp"] = sorted_ts[-1] if sorted_ts else ""
            non_mono = sum(1 for i in range(1, len(sorted_ts)) if sorted_ts[i] <= sorted_ts[i-1])
            result.metrics["non_monotonic"] = non_mono
            if non_mono:
                result.warnings.append("Non-monotonic timestamps: " + str(non_mono))
        else:
            result.metrics["first_timestamp"] = timestamps[0] if timestamps else ""
            result.metrics["last_timestamp"] = timestamps[-1] if timestamps else ""
        future = 0
        if warn_on_future_timestamps:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            future = len([t for t in timestamps if t > now])
            result.metrics["future_timestamps"] = future
            if future:
                result.warnings.append("Future timestamps: " + str(future))
        result.metrics["coverage_length"] = total
        score = 100
        if missing:
            score -= 20
        if duplicates:
            score -= min(duplicates * 2, 20)
        if malformed:
            score -= min(malformed * 3, 25)
        if anomalies:
            score -= min(anomalies * 3, 20)
        if non_mono:
            score -= min(non_mono * 2, 10)
        if future:
            score -= min(future * 2, 10)
        if total < minimum_rows:
            score -= 15
        score = max(0, min(100, score))
        result.score = score
        if score >= 90:
            result.grade = "A"
        elif score >= 80:
            result.grade = "B"
        elif score >= 70:
            result.grade = "C"
        elif score >= 60:
            result.grade = "D"
        else:
            result.grade = "F"
        return result
