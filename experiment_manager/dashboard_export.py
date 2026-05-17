"""
Dashboard-friendly JSON export.
Paper-only. No credentials. No broker data beyond CSV metadata.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


def export_dashboard_json(experiment_name, symbol_results, output_path):
    generated_at = datetime.now(timezone.utc).isoformat()

    dashboard = {
        "experiment_name": experiment_name,
        "generated_at": generated_at,
        "paper_only": True,
        "data_only": True,
        "summary": {
            "symbol_count": len(symbol_results),
            "consensus_long": sum(1 for s in symbol_results if s.get("consensus", {}).get("consensus_signal") == "LONG"),
            "consensus_short": sum(1 for s in symbol_results if s.get("consensus", {}).get("consensus_signal") == "SHORT"),
            "consensus_neutral": sum(1 for s in symbol_results if s.get("consensus", {}).get("consensus_signal") == "NEUTRAL"),
        },
        "symbols": [],
    }

    for sym_res in symbol_results:
        sym_entry = {
            "symbol": sym_res.get("symbol"),
            "timeframe": sym_res.get("timeframe"),
            "csv_source": sym_res.get("csv"),
            "validation_valid": sym_res.get("validation", {}).get("valid"),
            "consensus": sym_res.get("consensus", {}),
            "strategies": [
                {
                    "name": row.get("strategy"),
                    "signal": row.get("signal"),
                    "score": row.get("score"),
                    "weight": row.get("weight"),
                    "confidence": row.get("confidence"),
                }
                for row in sym_res.get("comparison", [])
            ],
        }
        dashboard["symbols"].append(sym_entry)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, default=str)

    return str(out)
