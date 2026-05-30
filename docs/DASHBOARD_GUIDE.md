# Dashboard Guide

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Starting the Dashboard

```bash
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json
```

## URL

Open your browser to:

```
http://127.0.0.1:8000
```

## Main Pages

### Home
- Overview of system status
- Latest readiness score
- Recent briefing summary

### Strategies
- List of available strategies
- Signal history
- Performance metrics

### Experiments
- Active and completed experiments
- Parameter sweep results
- Comparison charts

### Paper Portfolio
- Simulated positions
- PnL tracking
- Exposure breakdown

### Market Data
- Imported datasets
- Data quality status
- CSV import history

### Readiness
- Safety audit results
- Critical findings
- Warning summary

## Dashboard Properties

- **Read-only** — The dashboard displays data but does not trigger trades.
- **Local-only** — Runs on 127.0.0.1 by default. No external access.
- **No credentials required** — Uses local config only.
- **Stop with Ctrl+C** — Press Ctrl+C in the terminal to stop the server.

## Troubleshooting

- If port 8000 is in use, check for another Python process:
  ```bash
  lsof -i :8000
  kill -9 <PID>
  ```
- Ensure the virtual environment is activated.
- Verify `examples/local_app_config.example.json` exists.
