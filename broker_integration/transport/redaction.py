"""Credential and secret redaction utilities."""
import re
from typing import Dict, Any, Optional


def mask_account_id(account_id: str) -> str:
    if not account_id or len(account_id) <= 4:
        return "****"
    return "****" + account_id[-4:]


def redact_token(value: str) -> str:
    if not value or len(value) <= 8:
        return "****"
    return value[:4] + "****" + value[-4:]


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    secret_keys = {"authorization", "x-api-key", "api-key", "token", "x-auth-token"}
    result = {}
    for k, v in headers.items():
        if k.lower() in secret_keys:
            result[k] = redact_token(v)
        else:
            result[k] = v
    return result


def redact_url(url: str) -> str:
    """Remove query parameters that may contain secrets."""
    if "?" not in url:
        return url
    base, query = url.split("?", 1)
    safe_params = []
    for param in query.split("&"):
        if "=" in param:
            k, v = param.split("=", 1)
            if k.lower() in {"api_key", "token", "key", "secret", "auth"}:
                safe_params.append(f"{k}=****")
            else:
                safe_params.append(param)
        else:
            safe_params.append(param)
    return base + "?" + "&".join(safe_params)


def redact_secrets(obj: Any) -> Any:
    """Recursively redact secrets from dicts/lists."""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if isinstance(v, str) and any(s in k.lower() for s in {"api_key", "token", "secret", "password", "auth"}):
                result[k] = redact_token(v)
            else:
                result[k] = redact_secrets(v)
        return result
    elif isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    else:
        return obj
