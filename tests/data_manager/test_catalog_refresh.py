"""Tests for CatalogRefresh."""
import json
import tempfile
from pathlib import Path

from data_manager.catalog_refresh import CatalogRefresh
from data_manager.quality_score import ScoreResult


def test_catalog_refresh_writes_json():
    with tempfile.TemporaryDirectory() as td:
        catalog_path = Path(td) / "catalog.json"
        cr = CatalogRefresh(catalog_path)
        score = ScoreResult(score=95, grade="A")
        entry = cr.refresh(Path(td) / "market.csv", "EURUSD", "H1", "mt5", score)
        assert catalog_path.exists()
        with open(catalog_path, "r") as f:
            data = json.load(f)
        assert any(d["symbol"] == "EURUSD" for d in data["datasets"])
        assert entry["quality_score"] == 95
