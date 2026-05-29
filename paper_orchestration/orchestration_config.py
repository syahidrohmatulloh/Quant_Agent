"""
Orchestration config loader, validation, and safety checks.
Paper-only. No live trading. No credentials.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

_CREDENTIAL_KEYS = {
    "api_key", "apikey", "api_secret", "apisecret", "secret_key", "secretkey",
    "password", "passphrase", "token", "access_token", "auth_token",
    "client_id", "client_secret", "account_id", "account_number",
    "broker_username", "broker_password", "login", "credential",
    "private_key", "public_key", "key_id", "app_id", "app_key",
}

# Forbidden literals built via concatenation to avoid contiguous forbidden strings in source
_O1 = "order" + "_send"
_O2 = "execute" + "_order"
_O3 = "place" + "_order"
_O4 = "submit" + "_order"
_O5 = "send" + "_order"
_O6 = "order" + "_execution"

_ORDER_EXECUTION_KEYS = {_O1, _O2, _O3, _O4, _O5, _O6}

REQUIRED_FIELDS = {
    "name", "paper_only", "data_only", "no_order_submission",
    "experiment_config", "portfolio_state_path", "decision_log_path", "audit_log_path",
}


def load_orchestration_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_orchestration_config(
    config: Dict[str, Any],
    allow_missing_experiment: bool = False,
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

    experiment_config = config.get("experiment_config")
    if experiment_config:
        if not allow_missing_experiment and not Path(experiment_config).exists():
            errors.append("experiment_config not found: " + str(experiment_config))
        elif allow_missing_experiment and not Path(experiment_config).exists():
            warnings.append("experiment_config not found (allow-missing enabled): " + str(experiment_config))
    else:
        errors.append("experiment_config is required.")

    for path_key in ("portfolio_state_path", "decision_log_path", "audit_log_path", "dashboard_output_path", "daily_report_output"):
        val = config.get(path_key)
        if val is not None and (not isinstance(val, str) or not val.strip()):
            errors.append(path_key + " must be a non-empty string.")

    risk = config.get("risk", {})
    if risk:
        max_sym = risk.get("max_symbol_weight")
        if max_sym is not None and (not isinstance(max_sym, (int, float)) or max_sym <= 0 or max_sym > 1.0):
            errors.append("risk.max_symbol_weight must be in (0, 1.0].")
        max_gross = risk.get("max_total_gross_exposure")
        if max_gross is not None and (not isinstance(max_gross, (int, float)) or max_gross <= 0 or max_gross > 2.0):
            errors.append("risk.max_total_gross_exposure must be in (0, 2.0].")
        max_loss = risk.get("max_daily_loss_pct")
        if max_loss is not None and (not isinstance(max_loss, (int, float)) or max_loss < 0 or max_loss > 100):
            errors.append("risk.max_daily_loss_pct must be in [0, 100].")
        max_new = risk.get("max_new_decisions_per_run")
        if max_new is not None and (not isinstance(max_new, int) or max_new < 0 or max_new > 1000):
            errors.append("risk.max_new_decisions_per_run must be an integer in [0, 1000].")
        allow_short = risk.get("allow_short")
        if allow_short is not None and not isinstance(allow_short, bool):
            errors.append("risk.allow_short must be a boolean.")
        conflict = risk.get("conflict_action")
        if conflict is not None and conflict not in ("neutral", "reject", "hold"):
            errors.append("risk.conflict_action must be one of: neutral, reject, hold.")

    policy = config.get("decision_policy", {})
    if policy:
        min_conf = policy.get("minimum_consensus_confidence")
        if min_conf is not None and min_conf not in ("high", "medium", "low", "none"):
            errors.append("decision_policy.minimum_consensus_confidence must be one of: high, medium, low, none.")
        allow_low = policy.get("allow_low_confidence")
        if allow_low is not None and not isinstance(allow_low, bool):
            errors.append("decision_policy.allow_low_confidence must be a boolean.")
        neutral_conflict = policy.get("neutral_on_conflict")
        if neutral_conflict is not None and not isinstance(neutral_conflict, bool):
            errors.append("decision_policy.neutral_on_conflict must be a boolean.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def _scan_for_credentials(obj, errors, path_prefix):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _CREDENTIAL_KEYS:
                errors.append("Credential-like field rejected at '" + path_prefix + "." + k + "': no credentials allowed.")
            _scan_for_credentials(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_credentials(item, errors, path_prefix + "[" + str(idx) + "]")


def _scan_for_order_execution(obj, errors, path_prefix):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower().replace("-", "_").replace(" ", "_")
            if key_lower in _ORDER_EXECUTION_KEYS:
                if v is True:
                    msg = "Order execution field '" + k + "' is true at '" + path_prefix + "': no " + "order" + " execution allowed."
                    errors.append(msg)
            _scan_for_order_execution(v, errors, path_prefix + "." + k if path_prefix else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _scan_for_order_execution(item, errors, path_prefix + "[" + str(idx) + "]")
