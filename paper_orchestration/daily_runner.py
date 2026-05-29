"""
Daily paper workflow runner.
Orchestrates: config -> experiment -> consensus -> decisions -> risk -> portfolio -> audit -> dashboard -> report.
Paper-only. No live trading. No order submission.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from paper_orchestration.orchestration_config import load_orchestration_config, validate_orchestration_config
from paper_orchestration.paper_portfolio import PaperPortfolio
from paper_orchestration.paper_decision import build_paper_decisions, append_decisions
from paper_orchestration.risk_guard import RiskGuard
from paper_orchestration.audit_log import AuditLog
from paper_orchestration.dashboard_refresh import refresh_dashboard


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DailyRunner:
    """Run the full daily paper orchestration workflow."""

    def __init__(self, config_path: str, allow_missing_experiment: bool = False):
        self.config_path = config_path
        self.config = load_orchestration_config(config_path)
        self.allow_missing = allow_missing_experiment
        self.run_id = str(uuid.uuid4())[:8]

    def run(self) -> Dict[str, Any]:
        print("=" * 60)
        print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
        print("=" * 60)

        # 1. Validate orchestration config
        is_valid, errors, warnings = validate_orchestration_config(self.config, allow_missing_experiment=self.allow_missing)
        if not is_valid:
            print("Orchestration config validation failed:")
            for e in errors:
                print(" - " + e)
            raise ValueError("Config validation failed: " + "; ".join(errors))

        # 2. Initialize components
        portfolio = PaperPortfolio(
            state_path=self.config["portfolio_state_path"],
            cash_simulated=self.config.get("cash_simulated", 100000.0),
        )
        risk_guard = RiskGuard(self.config.get("risk", {}))
        audit = AuditLog(self.config["audit_log_path"])
        audit.record("config_loaded", self.run_id, {"config_path": self.config_path})

        # 3. Run experiment (Phase 13)
        audit.record("experiment_run_started", self.run_id, {"experiment_config": self.config["experiment_config"]})
        experiment_result = self._run_experiment()
        audit.record("experiment_run_completed", self.run_id, {"run_id": experiment_result.get("run_id")})

        # 4. Extract consensus results
        consensus_results = experiment_result.get("symbol_results", [])

        # 5. Build paper decisions
        decisions = build_paper_decisions(
            consensus_results=consensus_results,
            run_id=self.run_id,
            risk_config=self.config.get("risk", {}),
            decision_policy=self.config.get("decision_policy", {}),
        )
        audit.record("decisions_generated", self.run_id, {"decision_count": len(decisions)})

        # 6. Apply risk guard
        approved_decisions, risk_warnings, risk_errors = risk_guard.apply(decisions)
        audit.record("risk_guard_applied", self.run_id, {"warnings": risk_warnings, "errors": risk_errors})

        # 7. Update portfolio
        portfolio.update_positions(approved_decisions, run_id=self.run_id)
        audit.record("portfolio_updated", self.run_id, {"position_count": portfolio.summary()["position_count"]})

        # 8. Append decision log
        append_decisions(approved_decisions, self.config["decision_log_path"])

        # 9. Refresh dashboard
        dashboard_path = self.config.get("dashboard_output_path", "reports/dashboard/paper_orchestration/latest.json")
        refresh_dashboard(
            run_id=self.run_id,
            portfolio_summary=portfolio.summary(),
            latest_decisions=approved_decisions,
            risk_warnings=risk_warnings,
            audit_status="completed",
            output_path=dashboard_path,
        )
        audit.record("dashboard_refreshed", self.run_id, {"dashboard_path": dashboard_path})

        # 10. Generate daily report
        report_path = self._generate_report(experiment_result, approved_decisions, risk_warnings, portfolio.summary())
        audit.record("workflow_completed", self.run_id, {"report_path": report_path})

        print("\nDaily paper workflow complete.")
        print("Run ID: " + self.run_id)
        print("Portfolio state: " + self.config["portfolio_state_path"])
        print("Decision log: " + self.config["decision_log_path"])
        print("Audit log: " + self.config["audit_log_path"])
        print("Dashboard JSON: " + dashboard_path)
        print("Daily report: " + report_path)
        print("=" * 60)
        print("PAPER-ONLY / DATA-ONLY. No live trading. No order submission.")
        print("=" * 60)

        return {
            "run_id": self.run_id,
            "portfolio_state_path": self.config["portfolio_state_path"],
            "decision_log_path": self.config["decision_log_path"],
            "audit_log_path": self.config["audit_log_path"],
            "dashboard_path": dashboard_path,
            "report_path": report_path,
            "approved_decisions": approved_decisions,
            "risk_warnings": risk_warnings,
            "portfolio_summary": portfolio.summary(),
            "paper_only": True,
            "data_only": True,
            "no_order_submission": True,
        }

    def _run_experiment(self) -> Dict[str, Any]:
        """Run Phase 13 experiment using the configured experiment_config."""
        import sys
        from pathlib import Path
        project_root = Path(__file__).resolve().parents[1]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from experiment_manager.experiment_config import load_config as load_exp_config, validate_experiment_config
        from experiment_manager.experiment_runner import run_experiment

        exp_config_path = self.config["experiment_config"]
        exp_config = load_exp_config(exp_config_path)
        is_valid, errors, warnings = validate_experiment_config(exp_config, allow_missing_csv=self.allow_missing)
        if not is_valid:
            raise ValueError("Experiment config validation failed: " + "; ".join(errors))

        return run_experiment(
            config=exp_config,
            config_path=exp_config_path,
            output_dir=self.config.get("output_dir", "reports/experiments"),
            dashboard_dir=self.config.get("dashboard_dir", "reports/dashboard/experiments"),
        )

    def _generate_report(
        self,
        experiment_result: Dict[str, Any],
        decisions: List[Dict[str, Any]],
        risk_warnings: List[str],
        portfolio_summary: Dict[str, Any],
    ) -> str:
        report_path = self.config.get("daily_report_output", "reports/experiments/daily_paper_workflow_report.md")
        out = Path(report_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Daily Paper Workflow Report",
            "",
            "> **PAPER-ONLY / DATA-ONLY. No live trading. No order submission.**",
            "> **This report is for research and paper trading only. Not financial advice.**",
            "",
            "## Run Summary",
            "- **Run ID:** " + self.run_id,
            "- **Generated at:** " + _now_iso(),
            "- **Experiment:** " + experiment_result.get("experiment_name", "N/A"),
            "- **Experiment run_id:** " + experiment_result.get("run_id", "N/A"),
            "",
            "## Portfolio State",
            "- **Cash (simulated):** " + str(portfolio_summary.get("cash_simulated", 0)),
            "- **Gross exposure:** " + str(portfolio_summary.get("gross_exposure", 0)),
            "- **Net exposure:** " + str(portfolio_summary.get("net_exposure", 0)),
            "- **Position count:** " + str(portfolio_summary.get("position_count", 0)),
            "",
            "## Paper Decisions",
        ]
        for d in decisions:
            lines.append("- **" + d.get("symbol", "?") + "** | " + d.get("action", "?") + " | " + d.get("reason", ""))

        lines.append("")
        lines.append("## Risk Warnings")
        if risk_warnings:
            for w in risk_warnings:
                lines.append("- " + w)
        else:
            lines.append("- No risk warnings.")

        lines.append("")
        lines.append("## Output Paths")
        lines.append("- Portfolio state: `" + self.config["portfolio_state_path"] + "`")
        lines.append("- Decision log: `" + self.config["decision_log_path"] + "`")
        lines.append("- Audit log: `" + self.config["audit_log_path"] + "`")
        lines.append("- Dashboard JSON: `" + self.config.get("dashboard_output_path", "reports/dashboard/paper_orchestration/latest.json") + "`")
        lines.append("")
        lines.append("---")
        lines.append("Generated by Quant_Agent Phase 15 — Paper Trading Orchestration")

        report = "\n".join(lines)
        with open(out, "w", encoding="utf-8") as f:
            f.write(report)
        return str(out)
