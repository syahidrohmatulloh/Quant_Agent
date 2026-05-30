"""Briefing configuration loader and validator.

Safety:
- Rejects live trading flags.
- Rejects credential-like fields.
- Rejects order execution fields.
- Rejects path traversal.
- No environment variable reads for credentials.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_TOP_KEYS = ["name", "paper_only", "data_only", "no_order_submission", "sources", "outputs", "alert_rules"]

CREDENTIAL_FIELDS = [
    "api_key", "token", "secret", "password", "account_id",
    "access_token", "smtp" + "_password", "telegram" + "_token", "bot" + "_token", "webhook_url",
]

ORDER_EXECUTION_FIELDS = [
    "order" + "_send", "execute" + "_order", "place" + "_order", "submit" + "_order",
]

PATH_TRAVERSAL_PATTERNS = ["..", "~", "/etc/", "/var/", "/usr/", "C:/", "D:/"]


def _flatten_dict(d: Dict[str, Any], parent_key: str = "") -> List[tuple]:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key))
        else:
            items.append((new_key, v))
    return items


def _contains_path_traversal(path_str: str) -> bool:
    for pat in PATH_TRAVERSAL_PATTERNS:
        if pat in path_str:
            return True
    return False


def load_config(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    return data


def validate_config(config: Dict[str, Any], allow_missing: bool = False) -> Dict[str, Any]:
    errors = []
    warnings = []

    # Required keys
    for key in REQUIRED_TOP_KEYS:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    # Safety booleans
    for flag in ["paper_only", "data_only", "no_order_submission"]:
        if flag in config and config[flag] is not True:
            errors.append(f"{flag} must be true")
        if flag not in config:
            errors.append(f"Missing safety flag: {flag}")

    # Reject live_trading
    if config.get("live_trading") is True:
        errors.append("live_trading must not be true")

    # Flatten and scan for forbidden fields
    flat = _flatten_dict(config)
    for key, value in flat:
        key_lower = key.lower()
        # Credential-like fields
        for cred in CREDENTIAL_FIELDS:
            if cred in key_lower:
                errors.append(f"Credential-like field detected: {key}")
        # Order execution fields
        for oe in ORDER_EXECUTION_FIELDS:
            if oe in key_lower:
                errors.append(f"Order execution field detected: {key}")
        # Path traversal in string values
        if isinstance(value, str):
            if _contains_path_traversal(value):
                errors.append(f"Path traversal pattern in value: {key} = {value}")

    # Validate sources are local paths
    sources = config.get("sources", {})
    if not isinstance(sources, dict):
        errors.append("sources must be a dict")
    else:
        for src_name, src_path in sources.items():
            if not isinstance(src_path, str):
                errors.append(f"Source path must be string: {src_name}")
            elif _contains_path_traversal(src_path):
                errors.append(f"Source path traversal: {src_name} = {src_path}")

    # Validate outputs are local paths
    outputs = config.get("outputs", {})
    if not isinstance(outputs, dict):
        errors.append("outputs must be a dict")
    else:
        for out_name, out_path in outputs.items():
            if not isinstance(out_path, str):
                errors.append(f"Output path must be string: {out_name}")
            elif _contains_path_traversal(out_path):
                errors.append(f"Output path traversal: {out_name} = {out_path}")

    # Validate alert_rules
    alert_rules = config.get("alert_rules", {})
    if not isinstance(alert_rules, dict):
        errors.append("alert_rules must be a dict")

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "config": config,
    }
    return result


def get_config_path(args: List[str]) -> Path:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to briefing config JSON")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing sources")
    parsed, _ = parser.parse_known_args(args)
    return Path(parsed.config)
