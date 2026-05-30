# Command Cheat Sheet

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Tests

```bash
# Run all tests
python3 -m pytest tests/ -q

# Run specific phase tests
python3 -m pytest tests/readiness_gate/ -q
python3 -m pytest tests/docs/ -q
```

## Strategy Library

```bash
# Validate strategy library
python3 tools/validate_strategy_library.py
```

## CSV Workflow

```bash
# Run CSV signal generation
python3 tools/run_csv_signal.py --csv data/market/EURUSD.csv --strategy simple_ma

# Run CSV backtest
python3 tools/run_csv_backtest.py --csv data/market/EURUSD.csv --strategy simple_ma
```

## Experiment Manager

```bash
# Run experiment
python3 tools/run_experiment.py --config examples/experiment_config.example.json
```

## Paper Workflow

```bash
# Run paper orchestration
python3 tools/run_paper_orchestration.py --config examples/paper_orchestration_config.example.json

# Run paper simulator
python3 tools/run_paper_simulator.py --config examples/paper_simulator_config.example.json
```

## Briefing

```bash
# Generate daily briefing
python3 tools/generate_daily_briefing.py --config examples/briefing_config.example.json
```

## Local App

```bash
# Validate local app config
python3 tools/validate_local_app_config.py --config examples/local_app_config.example.json

# Run local workflow
python3 tools/run_local_workflow.py --config examples/local_app_config.example.json
```

## Readiness Audit

```bash
# Validate readiness config
python3 tools/validate_readiness_config.py --config examples/readiness_gate_config.example.json

# Run full readiness audit
python3 tools/run_readiness_audit.py --config examples/readiness_gate_config.example.json --allow-missing

# Check specific areas
python3 tools/check_paper_only_safety.py --config examples/readiness_gate_config.example.json
python3 tools/check_credential_exposure.py --config examples/readiness_gate_config.example.json
python3 tools/check_execution_gate.py --config examples/readiness_gate_config.example.json
```

## Dashboard

```bash
# Start local dashboard
python3 tools/run_local_dashboard.py --config examples/local_app_config.example.json

# Open in browser
open http://127.0.0.1:8000
```

## Scheduler

```bash
# Generate scheduler command (prints only, does not install)
python3 tools/generate_scheduler_command.py
```

## Cleanup

```bash
# Preview cleanup
python3 tools/cleanup_generated_outputs.py --dry-run

# Confirm cleanup
python3 tools/cleanup_generated_outputs.py --yes
```

## Documentation

```bash
# Validate documentation
python3 tools/validate_docs.py

# Show demo script
python3 tools/show_demo_script.py --summary

# Show command cheat sheet
python3 tools/show_command_cheatsheet.py --summary
```
