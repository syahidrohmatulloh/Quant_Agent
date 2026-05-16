"""Daily paper trading report generator."""
import os
import json
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class DailyReportGenerator:
    """Generates a comprehensive daily report from a session directory."""

    def __init__(self, session_dir: str, output_path: Optional[str] = None):
        self.session_dir = session_dir
        self.output_path = output_path or os.path.join(session_dir, "daily_report.md")

    def generate(self) -> Dict[str, Any]:
        summary = self._load_json("session_summary.json")
        audit_val = self._load_json("audit_validation.json")
        alerts = self._load_json("alerts.json") or []
        trades = self._load_csv("trades.csv") or []
        signals = self._load_csv("signals.csv") or []
        rejected = self._load_csv("rejected_signals.csv") or []

        report_lines = []
        report_lines.append("# Daily Paper Trading Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
        report_lines.append("")

        # 1. Executive summary
        report_lines.append("## 1. Executive Summary")
        report_lines.append(f"- Session ID: {summary.get('session_id', 'N/A')}")
        report_lines.append(f"- Cycles run: {summary.get('cycles_run', 0)}")
        report_lines.append(f"- Signals generated: {summary.get('signals_generated', 0)}")
        report_lines.append(f"- Signals rejected: {summary.get('signals_rejected', 0)}")
        report_lines.append(f"- Trades executed: {summary.get('trades_count', 0)}")
        report_lines.append("")

        # 2. Session configuration
        report_lines.append("## 2. Session Configuration")
        report_lines.append(f"- Starting balance: {summary.get('starting_balance', 0):,.2f}")
        report_lines.append(f"- Current balance: {summary.get('current_balance', 0):,.2f}")
        report_lines.append(f"- Symbols: {summary.get('symbols', ['EURUSD'])}")
        report_lines.append("")

        # 3. Model used
        report_lines.append("## 3. Model Used")
        report_lines.append(f"- Model ID: {summary.get('model_id', 'N/A')}")
        report_lines.append("")

        # 4. Approval status
        report_lines.append("## 4. Approval Status")
        report_lines.append(f"- Model approval: {summary.get('model_approval_status', 'unknown')}")
        report_lines.append("")

        # 5. Signals generated
        report_lines.append("## 5. Signals Generated")
        report_lines.append(f"- Total: {len(signals)}")
        if signals:
            report_lines.append("| Cycle | Symbol | Executed | Reason |")
            report_lines.append("|-------|--------|----------|--------|")
            for s in signals[:20]:
                report_lines.append(f"| {s.get('cycle_num', '-')} | {s.get('symbol', '-')} | {s.get('executed', False)} | {s.get('reason', '-')} |")
        report_lines.append("")

        # 6. Signals rejected by reason
        report_lines.append("## 6. Signals Rejected by Reason")
        reasons: Dict[str, int] = {}
        for r in rejected:
            reasons[r.get("reason", "unknown")] = reasons.get(r.get("reason", "unknown"), 0) + 1
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            report_lines.append(f"- {reason}: {count}")
        report_lines.append("")

        # 7. Orders created
        report_lines.append("## 7. Orders Created")
        report_lines.append(f"- Total paper orders: {len(trades)}")
        report_lines.append("")

        # 8. Trades closed
        report_lines.append("## 8. Trades Closed")
        report_lines.append(f"- Closed positions: {summary.get('closed_positions', 0)}")
        report_lines.append("")

        # 9. PnL summary
        report_lines.append("## 9. PnL Summary")
        report_lines.append(f"- Realized PnL: {summary.get('realized_pnl', 0):,.2f}")
        report_lines.append(f"- Unrealized PnL: {summary.get('unrealized_pnl', 0):,.2f}")
        report_lines.append("")

        # 10. Max drawdown
        report_lines.append("## 10. Max Drawdown")
        report_lines.append("- *Not yet computed in this session*")
        report_lines.append("")

        # 11. Exposure summary
        report_lines.append("## 11. Exposure Summary")
        report_lines.append(f"- Open positions: {summary.get('open_positions', 0)}")
        report_lines.append("")

        # 12. Alerts
        report_lines.append("## 12. Alerts")
        if alerts:
            for a in alerts:
                report_lines.append(f"- [{a.get('level', 'info').upper()}] {a.get('category', 'general')}: {a.get('message', '')}")
        else:
            report_lines.append("- No alerts generated.")
        report_lines.append("")

        # 13. Data quality issues
        report_lines.append("## 13. Data Quality Issues")
        report_lines.append("- *Review rejected_signals.csv for data-quality rejections.*")
        report_lines.append("")

        # 14. Audit validation result
        report_lines.append("## 14. Audit Validation Result")
        if audit_val:
            report_lines.append(f"- Valid: {audit_val.get('valid', False)}")
            report_lines.append(f"- Events checked: {audit_val.get('events_checked', 0)}")
            if audit_val.get("errors"):
                for err in audit_val["errors"]:
                    report_lines.append(f"  - Error: {err}")
        else:
            report_lines.append("- Audit validation not available.")
        report_lines.append("")

        # 15. Paper-only confirmation
        report_lines.append("## 15. Paper-Only Confirmation")
        report_lines.append(f"- **Paper-only mode: {summary.get('paper_only', True)}**")
        report_lines.append("- No live broker orders were executed during this session.")
        report_lines.append("")

        # 16. Next-day checklist
        report_lines.append("## 16. Next-Day Checklist")
        report_lines.append("- [ ] Review all rejected signals")
        report_lines.append("- [ ] Validate model drift metrics")
        report_lines.append("- [ ] Check data source health")
        report_lines.append("- [ ] Confirm paper broker balance reconciliation")
        report_lines.append("- [ ] Archive session artifacts")
        report_lines.append("")

        report_text = "\n".join(report_lines)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        return {
            "report_path": self.output_path,
            "summary": summary,
            "audit_valid": audit_val.get("valid") if audit_val else None,
            "alerts_count": len(alerts),
            "trades_count": len(trades)
        }

    def _load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.session_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def _load_csv(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        path = os.path.join(self.session_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
