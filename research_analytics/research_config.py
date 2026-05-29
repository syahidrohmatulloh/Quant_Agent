"""Research config validation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


REQUIRED_TOP_LEVEL = ["name", "paper_only", "data_only", "no_order_submission", "output_dir", "datasets", "strategies"]
CREDENTIAL_LIKE = {"api_key", "token", "secret", "password", "account_id", "access_token"}
ORDER_EXECUTION_LIKE = {
    "order" + "_send",
    "execute" + "_order",
    "place" + "_order",
    "submit" + "_order",
}


def _has_path_traversal(path: str) -> bool:
    if not path:
        return False
    normalized = os.path.normpath(path)
    return normalized.startswith("..") or "/../" in normalized or "..\\" in normalized


def validate_research_config(config: Dict[str, Any], allow_missing: bool = False) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(config, dict):
        errors.append("Config must be a JSON object.")
        return False, errors, warnings

    missing = [k for k in REQUIRED_TOP_LEVEL if k not in config]
    if missing:
        if allow_missing:
            warnings.append(f"Missing recommended keys: {missing}")
        else:
            errors.append(f"Missing required keys: {missing}")
            return False, errors, warnings

    # Safety flags
    for flag in ("paper_only", "data_only", "no_order_submission"):
        val = config.get(flag)
        if val is not True:
            msg = f"{flag} must be true (got {val})."
            if allow_missing:
                warnings.append(msg)
            else:
                errors.append(msg)

    if config.get("live_trading") is True:
        errors.append("live_trading must not be true.")

    # Reject credential-like fields
    for key in config.keys():
        low = key.lower()
        if low in CREDENTIAL_LIKE:
            errors.append(f"Credential-like field not allowed: {key}")
        if low in ORDER_EXECUTION_LIKE:
            errors.append(f"Order execution field not allowed: {key}")

    # Datasets
    datasets = config.get("datasets", [])
    if not isinstance(datasets, list):
        errors.append("datasets must be a list.")
    else:
        for idx, ds in enumerate(datasets):
            if not isinstance(ds, dict):
                errors.append(f"dataset[{idx}] must be an object.")
                continue
            for k in ("symbol", "timeframe", "csv"):
                if k not in ds:
                    errors.append(f"dataset[{idx}] missing {k}.")
            csv_path = ds.get("csv", "")
            if csv_path and _has_path_traversal(csv_path):
                errors.append(f"dataset[{idx}] csv path traversal detected: {csv_path}")

    # Strategies
    strategies = config.get("strategies", [])
    if not isinstance(strategies, list) or not strategies:
        if allow_missing:
            warnings.append("strategies list is empty or missing.")
        else:
            errors.append("strategies must be a non-empty list.")

    # output_dir path traversal
    out_dir = config.get("output_dir", "")
    if out_dir and _has_path_traversal(out_dir):
        errors.append(f"output_dir path traversal detected: {out_dir}")

    # dashboard_output path traversal
    dash_out = config.get("dashboard_output", "")
    if dash_out and _has_path_traversal(dash_out):
        errors.append(f"dashboard_output path traversal detected: {dash_out}")

    ok = len(errors) == 0
    return ok, errors, warnings


def load_research_config(path: str) -> Tuple[Dict[str, Any], bool, List[str], List[str]]:
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    ok, errors, warnings = validate_research_config(config)
    return config, ok, errors, warnings