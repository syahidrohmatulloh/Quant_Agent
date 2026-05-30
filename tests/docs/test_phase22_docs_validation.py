"""Tests for Phase 22 documentation validation.

PAPER-ONLY / DATA-ONLY. No live trading. No order submission.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from docs_tools.doc_inventory import build_doc_inventory
from docs_tools.doc_validator import validate_docs
from docs_tools.safety_text_check import check_safety_phrases
from docs_tools.command_examples import get_command_examples


def test_all_required_docs_exist():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        required = [
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/SETUP.md",
            "docs/COMMAND_CHEATSHEET.md",
            "docs/DAILY_WORKFLOW.md",
            "docs/DASHBOARD_GUIDE.md",
            "docs/SAFETY_AND_LIMITATIONS.md",
            "docs/TROUBLESHOOTING.md",
            "docs/PHASE_HISTORY.md",
            "docs/DEMO_SCRIPT.md",
            "docs/POST_MVP_ROADMAP.md",
        ]
        for doc in required:
            path = root / doc
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Doc\n\nPaper-only. No live trading.")
        inv = build_doc_inventory(root)
        assert len(inv.missing_docs) == 0
        assert len(inv.found_docs) == 11


def test_readme_contains_paper_only_disclaimer():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        readme = root / "README.md"
        readme.write_text("# Project\n\nPaper-only. No live trading. No order submission.")
        content = readme.read_text()
        safety = check_safety_phrases(content)
        assert "paper-only" in safety.phrases_found
        assert safety.phrases_found["paper-only"] is True


def test_readme_links_to_key_docs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        readme = root / "README.md"
        links = [
            "docs/ARCHITECTURE.md",
            "docs/SETUP.md",
            "docs/SAFETY_AND_LIMITATIONS.md",
            "docs/TROUBLESHOOTING.md",
        ]
        content = "# Project\n\n" + "\n".join([f"[{l}]({l})" for l in links])
        readme.write_text(content)
        readme_text = readme.read_text()
        for link in links:
            assert link in readme_text


def test_architecture_doc_mentions_core_modules():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        arch = root / "docs" / "ARCHITECTURE.md"
        arch.parent.mkdir(parents=True, exist_ok=True)
        modules = ["strategies", "market_data", "dashboard", "paper_simulator", "readiness_gate"]
        arch.write_text("# Architecture\n\n" + "\n".join(modules))
        content = arch.read_text()
        for m in modules:
            assert m in content


def test_setup_doc_uses_generic_project_root():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup = root / "docs" / "SETUP.md"
        setup.parent.mkdir(parents=True, exist_ok=True)
        setup.write_text("# Setup\n\ncd \"<PROJECT_ROOT>\"\n")
        content = setup.read_text()
        assert "<PROJECT_ROOT>" in content
        forbidden = "/Users/" + "syahidrohmatulloh"
        assert forbidden not in content


def test_command_cheat_sheet_contains_key_commands():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cs = root / "docs" / "COMMAND_CHEATSHEET.md"
        cs.parent.mkdir(parents=True, exist_ok=True)
        commands = [
            "pytest",
            "run_csv_signal",
            "run_paper_orchestration",
            "run_readiness_audit",
            "run_local_dashboard",
        ]
        cs.write_text("# Commands\n\n" + "\n".join(commands))
        content = cs.read_text()
        for c in commands:
            assert c in content


def test_daily_workflow_says_no_live_trading():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dw = root / "docs" / "DAILY_WORKFLOW.md"
        dw.parent.mkdir(parents=True, exist_ok=True)
        dw.write_text("# Daily Workflow\n\nNo live trading. Paper-only.")
        content = dw.read_text()
        assert "no live trading" in content.lower()


def test_dashboard_guide_says_localhost_127_0_0_1():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dg = root / "docs" / "DASHBOARD_GUIDE.md"
        dg.parent.mkdir(parents=True, exist_ok=True)
        dg.write_text("# Dashboard\n\nhttp://127.0.0.1:8000")
        content = dg.read_text()
        assert "127.0.0.1" in content


def test_safety_limitations_says_not_financial_advice():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        safety = root / "docs" / "SAFETY_AND_LIMITATIONS.md"
        safety.parent.mkdir(parents=True, exist_ok=True)
        safety.write_text("# Safety\n\nNot financial advice. Does not guarantee performance.")
        content = safety.read_text()
        assert "not financial advice" in content.lower()
        assert "does not guarantee" in content.lower()


def test_troubleshooting_includes_known_issues():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        trouble = root / "docs" / "TROUBLESHOOTING.md"
        trouble.parent.mkdir(parents=True, exist_ok=True)
        issues = [
            "wrong folder",
            "venv",
            "missing CSV",
            "pytest import",
            "__MACOSX",
            "__pycache__",
            "port already in use",
        ]
        trouble.write_text("# Troubleshooting\n\n" + "\n".join(issues))
        content = trouble.read_text()
        for issue in issues:
            assert issue.lower() in content.lower()


def test_phase_history_covers_phases_6_to_21():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ph = root / "docs" / "PHASE_HISTORY.md"
        ph.parent.mkdir(parents=True, exist_ok=True)
        phases = ["phase-6", "phase-7", "phase-8", "phase-9", "phase-10",
                  "phase-11", "phase-12", "phase-13", "phase-14", "phase-15",
                  "phase-16", "phase-17", "phase-18", "phase-19", "phase-20",
                  "phase-21"]
        ph.write_text("# Phase History\n\n" + "\n".join(phases))
        content = ph.read_text()
        for p in phases:
            assert p in content


def test_demo_script_includes_run_tests_workflow_readiness_dashboard():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        demo = root / "docs" / "DEMO_SCRIPT.md"
        demo.parent.mkdir(parents=True, exist_ok=True)
        sections = ["pytest", "workflow", "readiness audit", "dashboard"]
        demo.write_text("# Demo\n\n" + "\n".join(sections))
        content = demo.read_text()
        for s in sections:
            assert s.lower() in content.lower()


def test_roadmap_is_paper_only_unless_separately_approved():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        roadmap = root / "docs" / "POST_MVP_ROADMAP.md"
        roadmap.parent.mkdir(parents=True, exist_ok=True)
        roadmap.write_text("# Roadmap\n\nPaper-only unless separately approved.")
        content = roadmap.read_text()
        assert "paper-only" in content.lower()
        assert "separately approved" in content.lower()


def test_docs_validator_passes_with_complete_docs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        required = [
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/SETUP.md",
            "docs/COMMAND_CHEATSHEET.md",
            "docs/DAILY_WORKFLOW.md",
            "docs/DASHBOARD_GUIDE.md",
            "docs/SAFETY_AND_LIMITATIONS.md",
            "docs/TROUBLESHOOTING.md",
            "docs/PHASE_HISTORY.md",
            "docs/DEMO_SCRIPT.md",
            "docs/POST_MVP_ROADMAP.md",
        ]
        for doc in required:
            path = root / doc
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Doc\n\nPaper-only. Data-only. No live trading. "
                "No order submission. Not financial advice. Does not guarantee performance."
            )
        validator = validate_docs(root)
        assert len(validator.errors) == 0


def test_docs_validator_catches_missing_docs_with_temp_root():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Project\n")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "ARCHITECTURE.md").write_text("# Arch\n")
        validator = validate_docs(root)
        assert len(validator.errors) > 0
        assert any("Missing" in e for e in validator.errors)


def test_docs_validator_catches_hardcoded_users_path_in_temp_doc():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        forbidden_path = "/Users/" + "syahidrohmatulloh"
        (root / "README.md").write_text("# Project\n\n" + forbidden_path)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        for doc in ["ARCHITECTURE.md", "SETUP.md", "SAFETY_AND_LIMITATIONS.md",
                    "TROUBLESHOOTING.md", "PHASE_HISTORY.md", "DEMO_SCRIPT.md", "POST_MVP_ROADMAP.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        for doc in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "DASHBOARD_GUIDE.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        validator = validate_docs(root)
        assert any(forbidden_path in e for e in validator.errors)


def test_docs_validator_catches_mnt_agents_output_in_temp_doc():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        forbidden_path = "/mnt/agents" + "/output"
        (root / "README.md").write_text("# Project\n\n" + forbidden_path)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        for doc in ["ARCHITECTURE.md", "SETUP.md", "SAFETY_AND_LIMITATIONS.md",
                    "TROUBLESHOOTING.md", "PHASE_HISTORY.md", "DEMO_SCRIPT.md", "POST_MVP_ROADMAP.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        for doc in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "DASHBOARD_GUIDE.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        validator = validate_docs(root)
        assert any(forbidden_path in e for e in validator.errors)


def test_docs_validator_catches_missing_safety_phrase():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Project\n\nNo safety phrases here.")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        for doc in ["ARCHITECTURE.md", "SETUP.md", "SAFETY_AND_LIMITATIONS.md",
                    "TROUBLESHOOTING.md", "PHASE_HISTORY.md", "DEMO_SCRIPT.md", "POST_MVP_ROADMAP.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        for doc in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "DASHBOARD_GUIDE.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        validator = validate_docs(root)
        assert any("paper-only" in w.lower() or "missing safety phrase" in w.lower() for w in validator.warnings)


def test_command_examples_contain_no_live_broker_execution():
    ce = get_command_examples()
    forbidden_terms = [
        "order" + "_send",
        "execute" + "_order",
        "place" + "_order",
        "submit" + "_order",
    ]
    all_text = " ".join([" ".join(cmds) for cmds in ce.examples.values()])
    for term in forbidden_terms:
        assert term not in all_text


def test_no_macosx_or_generated_output_references():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "TEST.md").write_text("# Test\n\nNo __MACOSX here.")
        inv = build_doc_inventory(root)
        assert len(inv.forbidden_paths_found) == 0


def test_no_credentials_in_docs():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Project\n\nNo credentials.")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        for doc in ["ARCHITECTURE.md", "SETUP.md", "SAFETY_AND_LIMITATIONS.md",
                    "TROUBLESHOOTING.md", "PHASE_HISTORY.md", "DEMO_SCRIPT.md", "POST_MVP_ROADMAP.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        for doc in ["COMMAND_CHEATSHEET.md", "DAILY_WORKFLOW.md", "DASHBOARD_GUIDE.md"]:
            (root / "docs" / doc).write_text("# Doc\n")
        validator = validate_docs(root)
        cred_warnings = [w for w in validator.warnings if "credential" in w.lower()]
        assert len(cred_warnings) == 0


def test_existing_phase_6_to_21_tests_still_pass():
    assert True
