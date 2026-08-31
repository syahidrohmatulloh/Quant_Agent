# Demo Script

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Introduction

This demo script walks through a complete Quant_Agent presentation. It is designed for local demonstration on macOS with a zsh terminal.

## Safety Framing (30 seconds)

Begin every demo with:

> "Quant_Agent is a paper-only research tool. It does not trade live, does not submit orders, and does not provide financial advice. All results are simulated."

## Demo Flow

### Step 1: Run Tests (1 minute)

```bash
# Show the test suite passes
cd ""
source venv/bin/activate
python3 -m pytest tests/ -q
```

**Expected output:**
```
894 passed in X.XXs
```

**Talking point:** "The test suite validates every module. Each phase adds tests without breaking existing ones."

### Step 2: Validate Local App (30 seconds)

```bash
python3 tools/validate_local_app_config.py --config examples/local_app_config.example.json
```

**Expected output:**
```
OK: Local app config is valid.
```

**Talking point:** "Configuration validation ensures the system is safe before any workflow runs."

### Step 3: Run Local Workflow (1 minute)

```bash
python3 tools/run_local_workflow.py --config examples/local_app_config.example.json
```

**Expected output:**
- Workflow summary
- Reports generated in `reports/`
- Logs in `logs/`

**Talking point:** "The local workflow orchestrates data validation, signal generation, and paper decisions in one command."

### Step 4: Generate Briefing (30 seconds)

```bash
python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json
```

**Expected output:**
- Briefing text printed to console
- Saved to `reports/briefing/`

**Talking point:** "The daily briefing summarizes signals, exposures, and warnings for review."

### Step 5: Run Readiness Audit (1 minute)

```bash
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing
```

**Expected output:**
```
Readiness score: 95/100 (Grade A) — PAPER_MVP_READY
```

**Talking point:** "The readiness gate audits the system for safety. It checks for credentials, live trading code, and output hygiene. It explicitly does NOT approve live trading."

### Step 6: Run Release Candidate Check (30 seconds)

```bash
python3 tools/run_release_candidate_check.py --config examples/local_app_config.example.json --allow-missing
```

**Expected output:**
```
Status: READY or READY_WITH_WARNINGS
```

**Talking point:** "The release candidate check validates that the local MVP is safe, clean, test-passing, and ready to demo as a paper-only research system. It does not approve live trading."

### Step 7: Start Dashboard (30 seconds)

```bash
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json
```

**Expected output:**
```
Running on http://127.0.0.1:8000
```

**Talking point:** "The dashboard is local-only and read-only. It visualizes simulated results without executing trades."

### Step 8: Show Dashboard Screens (2 minutes)

Open `http://127.0.0.1:8000` and walk through:

1. **Home** — System status, readiness score, latest briefing
2. **Operator** — Daily workflow status and next commands
3. **Action Center** — Categorized warnings and action items
4. **Research Insights** — Strategy comparison and classifications
5. **Paper Runtime** — Session journal, signals, decisions, risk
6. **Data Quality** — CSV validation and quality issues
7. **Paper Broker** — Adapter validation and readiness
8. **Release Candidate** — Final demo safety and readiness check

**Talking point for each:** Explain that all numbers are simulated and no real money is involved.

## Closing (30 seconds)

End with limitations:

> "Quant_Agent is a research framework. It uses historical CSV data, simulates fills, and does not guarantee performance. Before any live trading discussion, separate legal, security, and compliance reviews are required."

## Quick Reference

```bash
# Full demo sequence
cd ""
source venv/bin/activate
python3 -m pytest tests/ -q
python3 tools/validate_local_app_config.py --config examples/local_app_config.example.json
python3 tools/run_local_workflow.py --config examples/local_app_config.example.json
python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing
python3 tools/run_release_candidate_check.py --config examples/local_app_config.example.json --allow-missing
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json
# Open http://127.0.0.1:8000
```
