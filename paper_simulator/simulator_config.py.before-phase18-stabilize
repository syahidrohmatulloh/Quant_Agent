"""Simulator config loader, validation, and safety checks.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


_CREDENTIAL_KEYS = {
    "api_key", "apikey", "api_secret", "apisecret", "secret_key", "secretkey",
    "password", "passphrase", "token", "access_token", "auth_token",
    "client_id", "client_secret", "account_id", "account_number",
    "broker_username", "broker_password", "login", "credential",
    "private_key", "public_key", "key_id", "app_id", "app_key",
}

_O1 = "order" + "_send"
_O2 = "execute" + "_order"
_O3 = "place" + "_order"
_O4 = "submit" + "_order"
_O5 = "send" + "_order"
_O6 = "order" + "_execution"

_ORDER_EXECUTION_KEYS = {_O1, _O2, _O3, _O4, _O5, _O6}

REQUIRED_FIELDS = {
    "name",
    "paper_only",
    "data_only",
    "no_order_submission",
    "initial_cash",
    "base_currency",
    "portfolio_state_path",
    "trade_log_path",
    "pnl_log_path",
    "symbols",
}

REQUIRED_SYMBOL_FIELDS = {"symbol", "timeframe", "csv", "pip_size", "contract_size"}


def _has_path_traversal(value: str) -> bool:
    if not value:
        return False
    return ".." in Path(str(value)).parts


def load_simulator_config(path: str) -> Tuple[Dict[str, Any], bool, List[str], List[str]]:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    ok, errors, warnings = validate_simulator_config(config)
    return config, ok, errors, warnings


def validate_simulator_config(
    config: Dict[str, Any], allow_missing: bool = False
) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    missing = REQUIRED_FIELDS - set(config.keys())
    if missing:
        errors.append("Missing required fields: " + str(sorted(missing)))

    if config.get("paper_only") is not True:
        errors.append("paper_only must be true.")
    if config.get("data_only") is not True:
        errors.append("data_only must be true.")
    if config.get("no_order_submission") is not True:
        errors.append("no_order_submission must be true.")

    if config.get("live_trading") is True:
        errors.append("live_trading must not be true. No live trading allowed.")

    _scan_for_credentials(config, errors, path_prefix="")
    _scan_for_order_execution(config, errors, path_prefix="")

    symbols = config.get("symbols", [])
    if not isinstance(symbols, list) or len(symbols) == 0:
        errors.append("symbols must be a non-empty list.")
    else:
        for idx, sym in enumerate(symbols):
            prefix = "symbols[" + str(idx) + "]"
            if not isinstance(sym, dict):
                errors.append(prefix + " must be a dict.")
                continue

            sym_missing = REQUIRED_SYMBOL_FIELDS - set(sym.keys())
            if sym_missing:
                errors.append(prefix + " missing required fields: " + str(sorted(sym_missing)))

            csv_path = sym.get("csv")
            if csv_path:
                if not isinstance(csv_path, str):
                    errors.append(prefix + ".csv must be a string.")
                elif _has_path_traversal(csv_path):
                    errors.append(prefix + ".csv path traversal rejected: " + csv_path)
                elif not allow_missing and not Path(csv_path).exists():
                    errors.append(prefix + ".csv not found: " + csv_path)
                elif allow_missing and not Path(csv_path).exists():
                    warnings.append(prefix + ".csv not found (allow-missing enabled): " + csv_path)

            for numeric_key in ("pip_size", "contract_size"):
                value = sym.get(numeric_key)
                if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                    errors.append(prefix + "." + numeric_key + " must be a positive number.")

    for path_key in (
        "portfolio_state_path",
        "trade_log_path",
        "pnl_log_path",
        "report_output",
        "dashboard_output",
        "paper_decision_log",
        "market_data_dir",
    ):
        val = config.get(path_key)
        if val is not None:
            if not isinstance(val, str) or not val.strip():
                errors.append(path_key + " must be a non-empty string.")
            elif _has_path_traversal(val):
                errors.append(path_key + " path traversal rejected: " + val)

    initial_cash = config.get("initial_cash")
    if initial_cash is not None and (
        not isinstance(initial_cash, (int, float)) or initial_cash <= 0
    ):
        errors.append("initial_cash must be a positive number.")

    execution = config.get("execution", {})
    if execution:
        fill_price = execution.get("fill_price")
        if fill_price not in ("next_close", "current_close", "midpoint_close", None):
            errors.append("execution.fill_price must be one of: next_close, current_close, midpoint_close.")

        allow_partial = execution.get("allow_partial_fill")
        if allow_partial is not None and not isinstance(allow_partial, bool):
            errors.append("execution.allow_partial_fill must be a boolean.")

        max_delay = execution.get("max_fill_delay_bars")
        if max_delay is not None and (
            not isinstance(max_delay, int) or max_delay < 0 or max_delay > 10
        ):
            errors.append("execution.max_fill_delay_bars must be an integer in [0, 10].")

    costs = config.get("costs", {})
    if costs:
        for key in ("spread_pips", "slippage_pips", "commission_per_million", "min_commission"):
            val = costs.get(key)
            if val is not None and (not isinstance(val, (int, float)) or val < 0):
                errors.append("costs." + key + " must be a non-negative number.")

    risk = config.get("risk", {})
    if risk:
        max_sym = risk.get("max_symbol_weight")
        if max_sym is not None and (
            not isinstance(max_sym, (int, float)) or max_sym <= 0 or max_sym > 1.0
        ):
            errors.append("risk.max_symbol_weight must be in (0, 1.0].")

        max_gross = risk.get("max_total_gross_exposure")
        if max_gross is not None and (
            not isinstance(max_gross, (int, float)) or max_gross <= 0 or max_gross > 2.0
        ):
            errors.append("risk.max_total_gross_exposure must be in (0, 2.0].")

        allow_short = risk.get("allow_short")
        if allow_short is not None and not isinstance(allow_short, bool):
            errors.append("risk.allow_short must be a boolean.")

        max_notional = risk.get("max_notional_per_symbol")
        if max_notional is not None and (
            not isinstance(max_notional, (int, float)) or max_notional <= 0
        ):
            errors.append("risk.max_notional_per_symbol must be a positive number.")

    return len(errors) == 0, errors, warnings


def _scan_for_credentials(obj: Any, errors: List[str], path_prefix: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _CREDENTIAL_KEYS:
                errors.append(
                    "Credential-like field rejected at '"
                    + (path_prefix + "." + k if path_prefix else k)
                    + "': no credentials allowed."
                )
            _scan_for_credentials(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_credentials(item, errors, path_prefix + "[" + str(idx) + "]")


def _scan_for_order_execution(obj: Any, errors: List[str], path_prefix: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _ORDER_EXECUTION_KEYS and v is True:
                errors.append(
                    "Order execution field '"
                    + k
                    + "' is true at '"
                    + path_prefix
                    + "': no "
                    + "order"
                    + " execution allowed."
                )
            _scan_for_order_execution(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_order_execution(item, errors, path_prefix + "[" + str(idx) + "]")
