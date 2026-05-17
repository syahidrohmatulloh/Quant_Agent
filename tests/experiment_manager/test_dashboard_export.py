"""
Test dashboard export.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import tempfile
from pathlib import Path
from experiment_manager.dashboard_export import export_dashboard_json


def test_dashboard_export_shape():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "dash.json")
        symbol_results = [
            {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "csv": "data/market/mt5_EURUSD_H1.csv",
                "validation": {"valid": True},
                "comparison": [
                    {"strategy": "ma_crossover", "signal": "LONG", "score": 0.8, "weight": 0.5, "confidence": "medium"}
                ],
                "consensus": {"consensus_signal": "LONG", "agreement_ratio": 1.0},
            }
        ]
        path = export_dashboard_json("test_exp", symbol_results, out_path)
        assert Path(path).exists()
        import json
        with open(path, "r") as f:
            data = json.load(f)
        assert data["experiment_name"] == "test_exp"
        assert data["paper_only"] is True
        assert data["summary"]["symbol_count"] == 1
        assert len(data["symbols"]) == 1
        assert data["symbols"][0]["strategies"][0]["name"] == "ma_crossover"
