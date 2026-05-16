"""Broker health check utilities."""
from typing import Dict, Any


def healthy(status: str = "ok", reason: str = "") -> Dict[str, Any]:
    return {"healthy": True, "status": status, "reason": reason}


def unhealthy(reason: str, status: str = "error") -> Dict[str, Any]:
    return {"healthy": False, "status": status, "reason": reason}
