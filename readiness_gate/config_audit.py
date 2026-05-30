"""Config completeness audit for example configs.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


class ConfigAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.warning_count: int = 0
        self.fail_count: int = 0


def _check_config(path: Path, required_keys: List[str]) -> Dict[str, Any]:
    result = {"path": str(path), "exists": path.exists(), "missing_keys": [], "credential_found": False, "live_trading_found": False}
    if not path.exists():
        return result
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return result
    text = json.dumps(cfg)
    for key in required_keys:
        if key not in text:
            result["missing_keys"].append(key)
    # Check for credentials
    cred_fragments = ["api_key", "api_secret", "password", "token", "secret"]
    for frag in cred_fragments:
        if frag in text.lower():
            result["credential_found"] = True
    if "live_trading" in text.lower():
        result["live_trading_found"] = True
    return result


def run_config_audit(project_root: Path, allow_missing: bool = False) -> ConfigAudit:
    audit = ConfigAudit()

    configs = [
        ("examples/paper_orchestration_config.example.json", ["paper_only", "mode"]),
        ("examples/market_data_import_config.example.json", ["source", "csv"]),
        ("examples/research_analytics_config.example.json", ["metrics"]),
        ("examples/paper_simulator_config.example.json", ["max_symbol_weight", "allow_short"]),
        ("examples/briefing_config.example.json", ["alerts"]),
        ("examples/local_app_config.example.json", ["host", "port"]),
    ]

    for rel_path, keys in configs:
        path = project_root / rel_path
        result = _check_config(path, keys)
        if not result["exists"]:
            if allow_missing:
                audit.findings.append({
                    "file": rel_path,
                    "status": "warning",
                    "message": "Optional config missing",
                })
                audit.warning_count += 1
            else:
                audit.findings.append({
                    "file": rel_path,
                    "status": "warning",
                    "message": "Required config missing",
                })
                audit.warning_count += 1
            continue

        if result["credential_found"]:
            audit.findings.append({
                "file": rel_path,
                "status": "fail",
                "message": "Credential-like value detected in config",
            })
            audit.fail_count += 1
        else:
            audit.findings.append({
                "file": rel_path,
                "status": "pass",
                "message": "No credential-like values detected",
            })
            audit.pass_count += 1

        if result["live_trading_found"]:
            audit.findings.append({
                "file": rel_path,
                "status": "fail",
                "message": "live_trading detected in config",
            })
            audit.fail_count += 1
        else:
            audit.findings.append({
                "file": rel_path,
                "status": "pass",
                "message": "No live_trading flag detected",
            })
            audit.pass_count += 1

        if result["missing_keys"]:
            audit.findings.append({
                "file": rel_path,
                "status": "warning",
                "message": f"Missing keys: {result['missing_keys']}",
            })
            audit.warning_count += 1
        else:
            audit.findings.append({
                "file": rel_path,
                "status": "pass",
                "message": "Required keys present",
            })
            audit.pass_count += 1

    return audit
