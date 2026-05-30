"""Tests for readiness report, dashboard, and log.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import tempfile
from pathlib import Path

from readiness_gate.readiness_report import generate_readiness_report
from readiness_gate.dashboard_export import export_dashboard, write_dashboard_json
from readiness_gate.readiness_log import append_readiness_log
from readiness_gate.readiness_score import compute_readiness_score, ReadinessScore
from readiness_gate.source_inventory import SourceInventory
from readiness_gate.safety_audit import SafetyAudit
from readiness_gate.credential_audit import CredentialAudit
from readiness_gate.execution_gate_audit import ExecutionGateAudit
from readiness_gate.risk_control_audit import RiskControlAudit
from readiness_gate.config_audit import ConfigAudit
from readiness_gate.output_hygiene_audit import OutputHygieneAudit
from readiness_gate.test_status_audit import ReadinessTestStatusAudit


def _make_score():
    return compute_readiness_score(
        source_inventory_pass=True,
        safety_pass_rate=1.0,
        credential_pass_rate=1.0,
        execution_gate_pass_rate=1.0,
        risk_control_pass_rate=1.0,
        config_pass_rate=1.0,
        output_hygiene_warnings=0,
        test_status_pass=True,
    )


def _make_empty_audit():
    inv = SourceInventory()
    safety = SafetyAudit()
    cred = CredentialAudit()
    exec_gate = ExecutionGateAudit()
    risk = RiskControlAudit()
    cfg = ConfigAudit()
    hygiene = OutputHygieneAudit()
    tests = ReadinessTestStatusAudit()
    return inv, safety, cred, exec_gate, risk, cfg, hygiene, tests


def test_readiness_report_writes_markdown_and_json():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        score = _make_score()
        inv, safety, cred, exec_gate, risk, cfg, hygiene, tests = _make_empty_audit()
        report = generate_readiness_report(root, score, inv, safety, cred, exec_gate, risk, cfg, hygiene, tests)
        assert "Quant_Agent MVP Readiness Gate Report" in report.markdown
        assert report.json_data["paper_only"] is True
        assert report.json_data["data_only"] is True
        assert report.json_data["no_order_submission"] is True
        assert "This readiness gate does not approve or enable live trading" in report.json_data["disclaimer"]


def test_dashboard_export_writes_expected_shape():
    score = _make_score()
    dashboard = export_dashboard(
        score=score,
        critical_count=0,
        warning_count=0,
        audit_summary={},
        top_findings=[],
        recommendations=[],
        warnings=[],
        errors=[],
    )
    assert dashboard.data["paper_only"] is True
    assert dashboard.data["data_only"] is True
    assert dashboard.data["no_order_submission"] is True
    assert "readiness_score" in dashboard.data
    assert "grade" in dashboard.data


def test_dashboard_export_writes_json_file():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "dashboard.json"
        score = _make_score()
        dashboard = export_dashboard(
            score=score,
            critical_count=0,
            warning_count=0,
            audit_summary={},
            top_findings=[],
            recommendations=[],
            warnings=[],
            errors=[],
        )
        write_dashboard_json(dashboard, path)
        data = json.loads(path.read_text())
        assert data["grade"] == score.grade


def test_readiness_log_appends_jsonl():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "log.jsonl"
        score = _make_score()
        log = append_readiness_log(path, score, 0, 0)
        assert path.exists()
        content = path.read_text()
        lines = content.strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["paper_only"] is True
        assert record["data_only"] is True
        assert record["no_order_submission"] is True
        assert record["score"] == score.score
        assert "readiness_id" in record
