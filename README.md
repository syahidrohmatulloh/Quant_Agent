# Quant_Agent

**Paper-Only / Data-Only Quantitative Research Assistant**

> **IMPORTANT:** Quant_Agent is strictly paper-only and data-only. It does not perform live trading, does not submit real-money orders, and does not connect to broker execution. It is not financial advice and does not guarantee performance. The readiness gate explicitly does not approve or enable live trading.

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

## What Quant_Agent Does NOT Do

- Live trading or real-money order submission
- Broker execution or order sending
- Real-time market data streaming (uses CSV files)
- Financial advice or profitability guarantees
- Cloud deployment (local-only by default)
- Credential storage or secret management

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
