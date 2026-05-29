"""Dashboard-friendly analytics export.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


def export_dashboard_json(
    config: Dict[str, Any],
    performance: Dict[str, Any],
    drawdown: Dict[str, Any],
    signal_quality: Dict[str, Any],
    regime_attribution: Dict[str, Any],
    strategy_attribution: Dict[str, Any],
    stability: Dict[str, Any],
    output_path: str,
) -> str:
    os.makedirs(Path(output_path).parent, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    all_warnings = []
    all_errors = []
    for section in (performance, drawdown, signal_quality, regime_attribution, strategy_attribution, stability):
        if isinstance(section, dict):
            all_warnings.extend(section.get("warnings", []))
            all_errors.extend(section.get("errors", []))

    payload = {
        "name": config.get("name", "research_analytics"),
        "generated_at": ts,
        "paper_only": True,
        "data_only": True,
        "no_order_submission": True,
        "datasets": config.get("datasets", []),
        "performance": performance,
        "drawdown": drawdown,
        "signal_quality": signal_quality,
        "regime_attribution": regime_attribution,
        "strategy_attribution": strategy_attribution,
        "stability": stability,
        "warnings": all_warnings,
        "errors": all_errors,
    }

    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
