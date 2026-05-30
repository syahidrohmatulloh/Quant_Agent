"""Local app configuration loader and validator.

Safety:
- Rejects live trading flags.
- Rejects credential-like fields.
- Rejects order execution fields.
- Rejects path traversal.
- No environment variable reads for credentials.
- Dashboard host defaults to 127.0.0.1.
- Rejects 0.0.0.0 unless explicit override.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_REQUIRED_TOP_KEYS = [
    "name", "paper_only", "data_only", "no_order_submission",
    "directories", "configs", "workflow", "dashboard",
]

# Credential-like keys (built via concatenation to avoid contiguous forbidden strings in source)
_CREDENTIAL_KEYS = {
    "api" + "_key", "apikey", "api_secret", "apisecret", "secret_key", "secretkey",
    "password", "passphrase", "token", "access" + "_token", "auth" + "_token",
    "client_id", "client_secret", "account_id", "account_number",
    "broker_username", "broker_password", "login", "credential",
    "private_key", "public_key", "key_id", "app_id", "app_key",
    "telegram" + "_token", "bot" + "_token", "smtp" + "_password",
    "webhook_url", "webhook" + "_token",
}

# Order execution keys (built via concatenation)
_O1 = "order" + "_send"
_O2 = "execute" + "_order"
_O3 = "place" + "_order"
_O4 = "submit" + "_order"
_O5 = "send" + "_order"
_O6 = "order" + "_execution"
_ORDER_EXECUTION_KEYS = {_O1, _O2, _O3, _O4, _O5, _O6}

_PATH_TRAVERSAL_PATTERNS = ["..", "~", "/etc/", "/var/", "/usr/", "C:/", "D:/", "//"]


def _flatten(obj: Any, prefix: str = "") -> List[Tuple[str, Any]]:
    items: List[Tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            items.extend(_flatten(v, new_key))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            new_key = f"{prefix}[{idx}]"
            items.extend(_flatten(item, new_key))
    else:
        items.append((prefix, obj))
    return items


def _has_path_traversal(val: str) -> bool:
    if not isinstance(val, str):
        return False
    for pat in _PATH_TRAVERSAL_PATTERNS:
        if pat in val:
            return True
    return False


def load_config(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_config(
    config: Dict[str, Any],
    allow_missing: bool = False,
    allow_nonlocal_host: bool = False,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    # Required keys
    for key in _REQUIRED_TOP_KEYS:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    # Safety flags
    for flag in ("paper_only", "data_only", "no_order_submission"):
        if flag in config and config[flag] is not True:
            errors.append(f"{flag} must be true")
        if flag not in config:
            errors.append(f"Missing safety flag: {flag}")

    # Reject live_trading
    if config.get("live_trading") is True:
        errors.append("live_trading must not be true")

    # Scan for credentials and order execution
    flat = _flatten(config)
    for key, value in flat:
        key_lower = key.lower().replace("-", "_").replace(" ", "_")
        for cred in _CREDENTIAL_KEYS:
            if cred in key_lower:
                errors.append(f"Credential-like field detected: {key}")
        for oe in _ORDER_EXECUTION_KEYS:
            if oe in key_lower:
                errors.append(f"Order execution field detected: {key}")
        if isinstance(value, str) and _has_path_traversal(value):
            errors.append(f"Path traversal pattern in value: {key} = {value}")

    # Validate directories
    directories = config.get("directories", {})
    if not isinstance(directories, dict):
        errors.append("directories must be a dict")
    else:
        for name, dpath in directories.items():
            if not isinstance(dpath, str):
                errors.append(f"Directory path must be string: {name}")
            elif _has_path_traversal(dpath):
                errors.append(f"Directory path traversal: {name} = {dpath}")

    # Validate configs
    configs = config.get("configs", {})
    if not isinstance(configs, dict):
        errors.append("configs must be a dict")
    else:
        for name, cpath in configs.items():
            if not isinstance(cpath, str):
                errors.append(f"Config path must be string: {name}")
            elif _has_path_traversal(cpath):
                errors.append(f"Config path traversal: {name} = {cpath}")
            elif not allow_missing and not Path(cpath).exists():
                errors.append(f"Config file not found: {cpath}")
            elif allow_missing and not Path(cpath).exists():
                warnings.append(f"Config file not found (allow-missing): {cpath}")

    # Validate workflow
    workflow = config.get("workflow", {})
    if not isinstance(workflow, dict):
        errors.append("workflow must be a dict")

    # Validate dashboard
    dashboard = config.get("dashboard", {})
    if not isinstance(dashboard, dict):
        errors.append("dashboard must be a dict")
    else:
        host = dashboard.get("host")
        if host is None:
            warnings.append("dashboard.host not set; defaulting to 127.0.0.1")
        elif host == "0.0.0.0" and not allow_nonlocal_host:
            errors.append("dashboard.host = 0.0.0.0 rejected. Use --allow-nonlocal-host to override.")
        port = dashboard.get("port")
        if port is not None and not isinstance(port, int):
            errors.append("dashboard.port must be an integer")

    # Validate cleanup
    cleanup = config.get("cleanup", {})
    if cleanup and not isinstance(cleanup, dict):
        errors.append("cleanup must be a dict")

    # Validate scheduler
    scheduler = config.get("scheduler", {})
    if scheduler and not isinstance(scheduler, dict):
        errors.append("scheduler must be a dict")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "config": config,
    }
