import os
import sys
import json
import pytest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_validation.session_report import DailyReportGenerator


class TestDailyReportGenerator:
    def test_report_generated(self):
        with tempfile.TemporaryDirectory() as td:
            summary = {
                "session_id": "sess-001", "cycles_run": 10,
                "signals_generated": 3, "signals_rejected": 7,
                "trades_count": 3, "starting_balance": 100000.0,
                "current_balance": 99950.0, "open_positions": 1,
                "closed_positions": 2, "realized_pnl": -50.0,
                "unrealized_pnl": 10.0, "paper_only": True,
                "model_id": "model-001", "model_approval_status": "approved"
            }
            with open(os.path.join(td, "session_summary.json"), "w") as f:
                json.dump(summary, f)
            with open(os.path.join(td, "audit_validation.json"), "w") as f:
                json.dump({"valid": True, "events_checked": 20}, f)
            with open(os.path.join(td, "alerts.json"), "w") as f:
                json.dump([], f)
            gen = DailyReportGenerator(td)
            result = gen.generate()
            assert os.path.exists(result["report_path"])
            with open(result["report_path"]) as f:
                text = f.read()
            assert "Daily Paper Trading Report" in text
            assert "Paper-Only Confirmation" in text

    def test_report_includes_paper_only_confirmation(self):
        with tempfile.TemporaryDirectory() as td:
            summary = {"session_id": "sess-001", "paper_only": True, "cycles_run": 5}
            with open(os.path.join(td, "session_summary.json"), "w") as f:
                json.dump(summary, f)
            with open(os.path.join(td, "audit_validation.json"), "w") as f:
                json.dump({"valid": True}, f)
            with open(os.path.join(td, "alerts.json"), "w") as f:
                json.dump([], f)
            gen = DailyReportGenerator(td)
            result = gen.generate()
            with open(result["report_path"]) as f:
                text = f.read()
            assert "paper-only mode: True" in text.lower() or "Paper-only mode: True" in text

    def test_report_includes_audit_validation(self):
        with tempfile.TemporaryDirectory() as td:
            summary = {"session_id": "sess-001", "paper_only": True, "cycles_run": 5}
            with open(os.path.join(td, "session_summary.json"), "w") as f:
                json.dump(summary, f)
            with open(os.path.join(td, "audit_validation.json"), "w") as f:
                json.dump({"valid": True, "events_checked": 15, "errors": []}, f)
            with open(os.path.join(td, "alerts.json"), "w") as f:
                json.dump([], f)
            gen = DailyReportGenerator(td)
            result = gen.generate()
            with open(result["report_path"]) as f:
                text = f.read()
            assert "Audit Validation Result" in text
            assert "Valid: True" in text

    def test_report_handles_no_trades(self):
        with tempfile.TemporaryDirectory() as td:
            summary = {"session_id": "sess-001", "cycles_run": 5, "trades_count": 0, "paper_only": True}
            with open(os.path.join(td, "session_summary.json"), "w") as f:
                json.dump(summary, f)
            with open(os.path.join(td, "audit_validation.json"), "w") as f:
                json.dump({"valid": True}, f)
            with open(os.path.join(td, "alerts.json"), "w") as f:
                json.dump([], f)
            gen = DailyReportGenerator(td)
            result = gen.generate()
            assert result["trades_count"] == 0
            with open(result["report_path"]) as f:
                text = f.read()
            assert "Trades executed: 0" in text

    def test_report_handles_rejected_signals(self):
        with tempfile.TemporaryDirectory() as td:
            summary = {"session_id": "sess-001", "cycles_run": 5, "signals_rejected": 5, "paper_only": True}
            with open(os.path.join(td, "session_summary.json"), "w") as f:
                json.dump(summary, f)
            with open(os.path.join(td, "audit_validation.json"), "w") as f:
                json.dump({"valid": True}, f)
            with open(os.path.join(td, "alerts.json"), "w") as f:
                json.dump([], f)
            with open(os.path.join(td, "rejected_signals.csv"), "w") as f:
                f.write("cycle_id,cycle_num,timestamp,symbol,reason\n")
                f.write("c1,0,2024-01-01T00:00:00+00:00,EURUSD,low_confidence\n")
                f.write("c2,1,2024-01-01T00:01:00+00:00,EURUSD,low_confidence\n")
            gen = DailyReportGenerator(td)
            result = gen.generate()
            with open(result["report_path"]) as f:
                text = f.read()
            assert "Signals Rejected by Reason" in text
            assert "low_confidence" in text
