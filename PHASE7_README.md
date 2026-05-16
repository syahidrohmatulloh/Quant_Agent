# Phase 7 — Paper Trading Runtime Validation

## New Modules

- `runtime_validation/` — Smoke tests, paper session runner, health checks, audit validator, dashboard validator, session reports, readiness checker
- `tests/runtime_validation/` — 7 test modules covering all Phase 7 components
- `tools/` — 6 new CLI tools for runtime operations
- `examples/` — Sample replay data and configs

## CLI Usage

### Smoke Test
```bash
python tools/run_runtime_smoke_test.py
```

### Paper Session
```bash
python tools/run_paper_session.py \
  --data examples/replay_fx_sample.csv \
  --config examples/paper_session_config.json \
  --cycles 100 \
  --output reports/session_001/
```

### Daily Report
```bash
python tools/generate_daily_report.py \
  --session-dir reports/session_001 \
  --output reports/session_001/daily_report.md
```

### Audit Validation
```bash
python tools/validate_audit_runtime.py \
  --audit-path data/audit.jsonl \
  --db-path data/quant_platform.db
```

### Dashboard Validation
```bash
python tools/validate_dashboard.py --in-process
```

### Readiness Check
```bash
python tools/check_readiness.py
```

## Test Command
```bash
python -m pytest tests/runtime_validation/ -v
```
