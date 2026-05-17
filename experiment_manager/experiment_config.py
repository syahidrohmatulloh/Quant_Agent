"""
Experiment config loader, validation, and safety checks.
Paper-only. No live trading. No credentials.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from strategies.registry import StrategyRegistry

_CREDENTIAL_KEYS = {
    "api_key", "apikey", "api_secret", "apisecret", "secret_key", "secretkey",
    "password", "passphrase", "token", "access_token", "auth_token",
    "client_id", "client_secret", "account_id", "account_number",
    "broker_username", "broker_password", "login", "credential",
    "private_key", "public_key", "key_id", "app_id", "app_key",
}

_DANGER_KEYS = {
    "live_trading", "order_send", "execute_order", "place_order",
    "submit_order", "send_order", "order_execution",
}

REQUIRED_FIELDS = {"name", "symbols", "strategies"}


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_experiment_config(
    config: Dict[str, Any],
    allow_missing_csv: bool = False,
) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    missing = REQUIRED_FIELDS - set(config.keys())
    if missing:
        errors.append("Missing required fields: " + str(sorted(missing)))

    if config.get("paper_only") is not True:
        errors.append("paper_only must be true (paper-only research only).")
    if config.get("data_only") is not True:
        errors.append("data_only must be true (data-only research only).")

    if config.get("live_trading") is True:
        errors.append("live_trading must not be true. No live trading allowed.")

    _scan_for_credentials(config, errors, path_prefix="")
    _scan_for_danger_keys(config, errors, path_prefix="")

    symbols = config.get("symbols", [])
    if not isinstance(symbols, list) or len(symbols) == 0:
        errors.append("symbols must be a non-empty list.")
    else:
        for idx, sym_entry in enumerate(symbols):
            prefix = "symbols[" + str(idx) + "]"
            if not isinstance(sym_entry, dict):
                errors.append(prefix + " must be an object.")
                continue
            if "symbol" not in sym_entry:
                errors.append(prefix + " missing 'symbol'.")
            if "timeframe" not in sym_entry:
                errors.append(prefix + " missing 'timeframe'.")
            if "csv" not in sym_entry:
                errors.append(prefix + " missing 'csv'.")
            else:
                csv_path = sym_entry["csv"]
                if not allow_missing_csv and not Path(csv_path).exists():
                    errors.append(prefix + " CSV not found: " + csv_path)
                elif allow_missing_csv and not Path(csv_path).exists():
                    warnings.append(prefix + " CSV not found (allow-missing enabled): " + csv_path)

    strategies = config.get("strategies", [])
    if not isinstance(strategies, list) or len(strategies) == 0:
        errors.append("strategies must be a non-empty list.")
    else:
        for idx, strat_entry in enumerate(strategies):
            prefix = "strategies[" + str(idx) + "]"
            if not isinstance(strat_entry, dict):
                errors.append(prefix + " must be an object.")
                continue
            if "name" not in strat_entry:
                errors.append(prefix + " missing 'name'.")
                continue
            strat_name = strat_entry["name"]
            if not StrategyRegistry.is_registered(strat_name):
                errors.append(
                    "Unknown strategy '" + strat_name + "'. Available: " + str(StrategyRegistry.list_strategies())
                )

    consensus = config.get("consensus")
    if consensus is not None:
        method = consensus.get("method", "majority_vote")
        valid_methods = {"majority_vote", "weighted_vote", "conservative", "unanimous_only"}
        if method not in valid_methods:
            errors.append("consensus.method must be one of " + str(valid_methods) + ", got '" + method + "'.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def _scan_for_credentials(obj: Any, errors: List[str], path_prefix: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _CREDENTIAL_KEYS:
                errors.append("Credential-like field rejected at '" + path_prefix + "." + k + "': no credentials allowed.")
            _scan_for_credentials(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_credentials(item, errors, path_prefix + "[" + str(idx) + "]")
    elif isinstance(obj, str):
        pass


def _scan_for_danger_keys(obj: Any, errors: List[str], path_prefix: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _DANGER_KEYS:
                if v is True:
                    errors.append("Dangerous field '" + k + "' is true at '" + path_prefix + "': no live trading or order execution allowed.")
            _scan_for_danger_keys(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_danger_keys(item, errors, path_prefix + "[" + str(idx) + "]")
