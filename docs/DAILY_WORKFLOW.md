# Daily Workflow

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Recommended Daily Sequence

### 1. Update/Import Data Manually

```bash
# Import new CSV market data
python3 tools/import_csv_market_data.py --csv data/raw_imports/EURUSD_2024.csv --pair EURUSD

# Validate imported data
python3 tools/validate_market_data.py --dataset EURUSD
```

### 2. Run Experiment

```bash
# Run strategy experiment
python3 tools/run_experiment.py --config examples/experiment_config.example.json
```

### 3. Run Paper Orchestration

```bash
# Generate paper trading decisions
python3 tools/run_paper_orchestration.py --config examples/paper_orchestration_config.example.json
```

### 4. Run Paper Simulator

```bash
# Simulate portfolio performance
python3 tools/run_paper_simulator.py --config examples/paper_simulator_config.example.json
```

### 5. Generate Briefing

```bash
# Generate daily briefing text
python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json
```

### 6. Run Readiness Audit (Optional)

```bash
# Run readiness audit if you changed code
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing
```

### 7. Review Dashboard

```bash
# Start dashboard
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json

# Open browser
open http://127.0.0.1:8000
```

## Important Notes

- This workflow is entirely paper-only. No live trading occurs.
- All data is CSV-based. No live market data streaming.
- Cron scheduling is optional and must be configured manually. The scheduler tool only prints commands.
- Review outputs in `reports/` and `logs/` before making any decisions.
- The readiness gate explicitly does not approve or enable live trading.
