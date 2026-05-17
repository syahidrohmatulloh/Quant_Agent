"""
Test experiment config validation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from experiment_manager.experiment_config import validate_experiment_config


def _valid_config():
    return {
        "name": "test_experiment",
        "paper_only": True,
        "data_only": True,
        "symbols": [
            {"symbol": "EURUSD", "timeframe": "H1", "csv": "dummy.csv"}
        ],
        "strategies": [
            {"name": "ma_crossover", "params": {"fast": 5, "slow": 20}}
        ],
        "backtest": False,
        "consensus": {"method": "majority_vote", "minimum_agreement": 0.6},
    }


def test_config_loads_valid_json():
    config = _valid_config()
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is True
    assert len(errors) == 0


def test_missing_required_fields():
    config = {}
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("Missing required fields" in e for e in errors)


def test_paper_only_false_rejected():
    config = _valid_config()
    config["paper_only"] = False
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("paper_only must be true" in e for e in errors)


def test_data_only_false_rejected():
    config = _valid_config()
    config["data_only"] = False
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("data_only must be true" in e for e in errors)


def test_unknown_strategy_name_rejected():
    config = _valid_config()
    config["strategies"] = [{"name": "nonexistent_strategy"}]
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("Unknown strategy" in e for e in errors)


def test_credential_like_fields_rejected():
    config = _valid_config()
    config["api_key"] = "secret123"
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("Credential-like field" in e for e in errors)


def test_live_trading_true_rejected():
    config = _valid_config()
    config["live_trading"] = True
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is False
    assert any("live_trading" in e for e in errors)


def test_missing_csv_rejected_by_default():
    config = _valid_config()
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=False)
    assert is_valid is False
    assert any("CSV not found" in e for e in errors)


def test_allow_missing_csv_preview():
    config = _valid_config()
    is_valid, errors, warnings = validate_experiment_config(config, allow_missing_csv=True)
    assert is_valid is True
    assert any("allow-missing" in w for w in warnings)
