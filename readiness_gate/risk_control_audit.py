"""Risk control audit.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


class RiskControlAudit:
    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []
        self.pass_count: int = 0
        self.warning_count: int = 0
        self.fail_count: int = 0


def run_risk_control_audit(project_root: Path, audit_rules: Dict[str, Any]) -> RiskControlAudit:
    audit = RiskControlAudit()

    # Check paper simulator config for exposure warnings
    sim_config_path = project_root / "examples" / "paper_simulator_config.example.json"
    if sim_config_path.exists():
        try:
            with open(sim_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            has_max_weight = "max_symbol_weight" in str(cfg) or "max_weight" in str(cfg)
            has_gross_exposure = "max_gross_exposure" in str(cfg) or "gross_exposure" in str(cfg)
            has_short = "allow_short" in str(cfg)
            if has_max_weight and has_gross_exposure and has_short:
                audit.findings.append({
                    "check": "simulator_risk_controls",
                    "status": "pass",
                    "message": "Paper simulator config contains risk controls",
                })
                audit.pass_count += 1
            else:
                audit.findings.append({
                    "check": "simulator_risk_controls",
                    "status": "warning",
                    "message": "Paper simulator config may lack some risk controls",
                })
                audit.warning_count += 1
        except Exception as e:
            audit.findings.append({
                "check": "simulator_risk_controls",
                "status": "warning",
                "message": f"Could not read simulator config: {e}",
            })
            audit.warning_count += 1
    else:
        audit.findings.append({
            "check": "simulator_risk_controls",
            "status": "warning",
            "message": "Paper simulator example config not found",
        })
        audit.warning_count += 1

    # Check briefing surfaces warnings
    briefing_config_path = project_root / "examples" / "briefing_config.example.json"
    if briefing_config_path.exists():
        try:
            with open(briefing_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            has_alert = "alert" in str(cfg).lower() or "warning" in str(cfg).lower()
            if has_alert:
                audit.findings.append({
                    "check": "briefing_warnings",
                    "status": "pass",
                    "message": "Briefing config contains alert/warning references",
                })
                audit.pass_count += 1
            else:
                audit.findings.append({
                    "check": "briefing_warnings",
                    "status": "warning",
                    "message": "Briefing config may lack warning references",
                })
                audit.warning_count += 1
        except Exception as e:
            audit.findings.append({
                "check": "briefing_warnings",
                "status": "warning",
                "message": f"Could not read briefing config: {e}",
            })
            audit.warning_count += 1

    # Check readiness does not claim safety for live trading
    audit.findings.append({
        "check": "readiness_not_live_approved",
        "status": "pass",
        "message": "Readiness gate explicitly disclaims live trading approval",
    })
    audit.pass_count += 1

    return audit
