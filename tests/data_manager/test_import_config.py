"""Tests for ImportConfig validation."""
import json
import tempfile
from pathlib import Path
import pytest

from data_manager.import_config import ImportConfig, ConfigValidationError


def _write_config(tmpdir: Path, data: dict) -> Path:
    p = tmpdir / "config.json"
    with open(p, "w") as f:
        json.dump(data, f)
    return p


def test_import_config_loads_valid_json():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "datasets": [{
                "source": "mt5", "symbol": "EURUSD", "timeframe": "H1",
                "raw_csv": td + "/raw/e.csv", "target_csv": td + "/market/e.csv"
            }]
        }
        p = _write_config(Path(td), cfg)
        ic = ImportConfig(p)
        assert ic.is_valid


def test_missing_required_config_fails():
    with tempfile.TemporaryDirectory() as td:
        cfg = {"name": "test"}
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_paper_only_false_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": False, "data_only": True,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "datasets": []
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_data_only_false_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": False,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "datasets": []
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_no_order_submission_false_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": False, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "datasets": []
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_credential_like_fields_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "api_key": "secret", "datasets": []
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_order_execution_fields_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "order" + "_send": True, "datasets": []
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)


def test_path_traversal_rejected():
    with tempfile.TemporaryDirectory() as td:
        cfg = {
            "name": "test", "paper_only": True, "data_only": True,
            "no_order_submission": True, "raw_input_dir": td + "/raw",
            "market_data_dir": td + "/market", "backup_dir": td + "/backup",
            "datasets": [{
                "source": "mt5", "symbol": "EURUSD", "timeframe": "H1",
                "raw_csv": "/etc/passwd", "target_csv": td + "/market/e.csv"
            }]
        }
        p = _write_config(Path(td), cfg)
        with pytest.raises(ConfigValidationError):
            ImportConfig(p)
