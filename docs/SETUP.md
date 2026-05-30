# Setup Guide

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Requirements

- macOS
- zsh terminal
- Python 3.10+
- Git

## Installation

```bash
# 1. Navigate to project root
cd "<PROJECT_ROOT>"

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

## Verify Installation

```bash
# Run the test suite
python3 -m pytest tests/ -q
```

Expected: all tests pass with 0 failures.

## Folder Structure

```
<PROJECT_ROOT>/
  venv/                  — Python virtual environment
  strategies/            — Strategy library
  strategy_lab/          — Strategy tools
  market_data/           — Market data handlers
  strategy_runtime/      — Runtime engine
  experiment_manager/    — Experiment tracking
  dashboard/             — Local dashboard
  paper_orchestration/   — Paper workflow
  data_manager/          — Dataset manager
  research_analytics/    — Analytics
  paper_simulator/       — Simulator
  briefing/              — Briefing generator
  local_app/             — App launcher
  readiness_gate/        — Safety audit
  tools/                 — CLI tools
  tests/                 — Test suite
  examples/              — Example configs
  docs/                  — Documentation
  reports/               — Generated reports (gitignored)
  logs/                  — Generated logs (gitignored)
  data/market/           — Market data (gitignored)
  local_configs/         — Local configs (gitignored)
```

## Important Notes

- No credentials are required to run tests.
- No live broker setup is required.
- All commands are relative to the project root.
- MetaTrader5 pip package is not available on macOS; use CSV workflow instead.
- Example configs are in `examples/` — copy and customize for local use.
