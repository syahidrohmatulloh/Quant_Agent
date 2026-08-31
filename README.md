# Quant_Agent

**Paper-Only / Data-Only Quantitative Research Assistant**

> **IMPORTANT:** Quant_Agent is strictly paper-only and data-only. It does not perform live real-money trading. Internal simulation is the default; sandbox/practice broker integrations are isolated, explicitly gated, and must never target live endpoints. It is not financial advice and does not guarantee performance. The readiness gate does not approve or enable live trading.

## Overview

Quant_Agent is a modular Python project for quantitative strategy research, backtesting, and paper-trading simulation. It is designed for local use on macOS with a zsh terminal and Python virtual environment.

## What Quant_Agent Does

- Strategy library with institutional-style signal generation
- CSV market data workflow and validation
- MetaTrader 5 market data integration (CSV export)
- Strategy experiment manager for parameter sweeps
- Local quant dashboard for visualizing results
- Paper trading orchestration and simulation
- Dataset manager for real market data imports
- Research analytics and attribution
- Daily briefing generation
- Readiness gate and safety audit
- One-command local app launcher
- Paper runtime/session journal, data-quality center, and research insights
- Explicitly gated sandbox/practice broker integrations for testing only
- Quant correctness regression checks for accounting, exposure, causality, and risk

## What Quant_Agent Does NOT Do

- Live real-money trading or live-endpoint order submission
- Treat sandbox/practice execution as approval for live trading
- Guarantee strategy profitability or provide financial advice
- Store real credentials in source code, examples, tests, logs, or reports
- Bypass paper-only readiness, risk, or execution gates

Quant_Agent contains market-data streaming components and sandbox/practice broker adapters. External practice-order submission, where supported, is opt-in and must remain isolated from live endpoints.

## Main Capabilities by Phase

| Phase | Capability |
|-------|-----------|
| Phase 6 | Baseline architecture and tests |
| Phase 7 | Runtime validation and safety |
| Phase 8 | Broker integration (paper-only adapters) |
| Phase 9 | OANDA practice transport and dry-run safety |
| Phase 10 | Institutional-style strategy library |
| Phase 11 | MetaTrader 5 market data integration |
| Phase 12 | Real market CSV workflow and strategy runtime |
| Phase 13 | Strategy experiment manager |
| Phase 14 | Local quant dashboard UI |
| Phase 15 | Paper trading orchestration |
| Phase 16 | Real market data import and dataset manager |
| Phase 17 | Research analytics and attribution |
| Phase 18 | Paper portfolio simulator v2 |
| Phase 19 | Alerting and daily briefing |
| Phase 20 | Robust local app packaging and launcher |
| Phase 21 | Live-readiness gate and safety audit |
| Phase 22 | Documentation, user manual, and demo script |
| Phase 23 | Readiness warning cleanup and execution-gate hardening |
| Phase 24 | Operator one-command workflow |
| Phase 25 | Operator Action Center |
| Phase 26 | Research Insights |
| Phase 27 | Paper Runtime session journal |
| Phase 28 | Local Data Quality Center |
| Phase 29 | Paper Broker readiness hardening |
| Phase 30 | Local MVP release-candidate hardening |
| Phase 30A | Quant correctness & reliability hardening |

## Quant Correctness Baseline (Phase 30A)

Phase 30A hardens numerical and safety invariants before further execution features are added. The regression suite covers exposure notional, realized/unrealized PnL and transaction costs, causal `next_close` fills, closed-position cleanup, repeated-fill aggregation, risk input validation, timeframe-aware performance annualization, audit-chain continuity, binary signal-label mapping, and paper/practice readiness boundaries.

The project remains paper-only/data-only. A green release-candidate checklist is not a substitute for quantitative correctness tests.

## Quick Start

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd Quant_Agent

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
python3 -m pytest tests/ -q

# 5. Validate local app config
python3 tools/validate_local_app_config.py --config examples/local_app_config.example.json

# 6. Initialize directories
python3 tools/init_local_directories.py

# 7. Run local workflow
python3 tools/run_local_workflow.py --config examples/local_app_config.example.json

# 8. Run readiness audit
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing

# 9. Start dashboard
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json
# Open http://127.0.0.1:8000 in your browser
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and data flow
- [Setup](docs/SETUP.md) — Installation and environment setup
- [Command Cheat Sheet](docs/COMMAND_CHEATSHEET.md) — Common commands
- [Daily Workflow](docs/DAILY_WORKFLOW.md) — Recommended daily sequence
- [Dashboard Guide](docs/DASHBOARD_GUIDE.md) — Using the local dashboard
- [Safety and Limitations](docs/SAFETY_AND_LIMITATIONS.md) — Important safety information
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Common issues and fixes
- [Phase History](docs/PHASE_HISTORY.md) — Development timeline
- [Demo Script](docs/DEMO_SCRIPT.md) — Presentation demo flow
- [Post-MVP Roadmap](docs/POST_MVP_ROADMAP.md) — Future directions

## Safety

Quant_Agent is a research tool. It simulates trading decisions on historical and CSV-imported data. It does not:
- Submit orders to brokers
- Manage real money
- Provide investment advice
- Guarantee returns

Before any future live trading discussion, a separate design review, legal/compliance review, security audit, broker sandbox testing, risk kill-switch implementation, manual approval, and independent validation are required.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.

## Roadmap

See [docs/POST_MVP_ROADMAP.md](docs/POST_MVP_ROADMAP.md) for future phases.

## License

This project is for educational and research purposes only.
