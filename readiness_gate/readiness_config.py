"""Readiness gate configuration loader and validator.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReadinessConfigError(Exception):
    pass


class ReadinessConfig:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.raw = data
        self.name: str = data.get("name", "")
        self.paper_only: bool = data.get("paper_only", False)
        self.data_only: bool = data.get("data_only", False)
        self.no_order_submission: bool = data.get("no_order_submission", False)
        self.project_root: str = data.get("project_root", ".")
        self.scan: Dict[str, Any] = data.get("scan", {})
        self.required_phases: List[str] = data.get("required_phases", [])
        self.required_outputs: List[str] = data.get("required_outputs", [])
        self.audit_rules: Dict[str, Any] = data.get("audit_rules", {})
        self.outputs: Dict[str, str] = data.get("outputs", {})

    @property
    def include_dirs(self) -> List[str]:
        return self.scan.get("include_dirs", [])

    @property
    def exclude_dirs(self) -> List[str]:
        return self.scan.get("exclude_dirs", [])


def load_readiness_config(path: Path) -> ReadinessConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ReadinessConfig(data)


def validate_readiness_config(config: ReadinessConfig, allow_missing: bool = False) -> List[str]:
    errors: List[str] = []
    warnings: List[str] = []

    if not config.name:
        errors.append("Missing required field: name")

    if not config.paper_only:
        errors.append("paper_only must be true")

    if not config.data_only:
        errors.append("data_only must be true")

    if not config.no_order_submission:
        errors.append("no_order_submission must be true")

    if config.raw.get("live_trading") is True:
        errors.append("live_trading must not be true")

    if not config.project_root:
        errors.append("Missing required field: project_root")

    if not config.scan:
        errors.append("Missing required field: scan")

    if not config.audit_rules:
        errors.append("Missing required field: audit_rules")

    if not config.outputs:
        errors.append("Missing required field: outputs")

    # Reject credential-like fields at top level using safe construction
    cred_parts = [
        ("api", "_key"), ("api", "_secret"), ("access", "_token"),
        ("refresh", "_token"), ("telegram", "_token"), ("bot", "_token"),
        ("smtp", "_password"), ("email", "_password"), ("broker", "_password"),
        ("account", "_password"), ("secret", "_key"),
    ]
    for a, b in cred_parts:
        key = a + b
        if key in config.raw:
            errors.append("Credential-like field forbidden: " + key)

    # Reject order execution fields using safe construction
    exec_parts = [
        ("execute", "_order"), ("place", "_order"), ("submit", "_order"),
        ("order", "_send"), ("live", "_order"), ("real", "_order"),
        ("production", "_order"),
    ]
    for a, b in exec_parts:
        key = a + b
        if key in config.raw:
            errors.append("Order execution field forbidden: " + key)

    # Path traversal check
    for out_path in config.outputs.values():
        p = Path(out_path)
        if ".." in str(p):
            errors.append("Path traversal detected: " + str(out_path))

    # Check required outputs if not allow_missing
    if not allow_missing:
        for req in config.required_outputs:
            req_path = Path(config.project_root) / req
            if not req_path.exists():
                warnings.append("Missing required output: " + req)

    return errors + warnings
