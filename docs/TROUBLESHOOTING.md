# Troubleshooting

> **PAPER-ONLY / DATA-ONLY.** No live trading. No order submission. Not financial advice.

## Common Issues

### Running Commands from Wrong Folder

**Symptom:** `ModuleNotFoundError` or file not found errors.

**Fix:**
```bash
cd "<PROJECT_ROOT>"
pwd  # Should show your project root
```

### Virtual Environment Not Activated

**Symptom:** `python3: command not found` or wrong Python version.

**Fix:**
```bash
source venv/bin/activate
which python3  # Should show venv path
```

### MetaTrader5 pip Not Available on Mac

**Symptom:** `pip install MetaTrader5` fails on macOS.

**Fix:** Use CSV workflow instead. Export data from MT5 desktop as CSV and import:
```bash
python3 tools/import_csv_market_data.py --csv data/raw_imports/EURUSD.csv --pair EURUSD
```

### Missing CSV Data / Market Files

**Symptom:** `FileNotFoundError: data/market/EURUSD.csv`

**Fix:**
```bash
# Check data directory
ls data/market/

# Import data if missing
python3 tools/import_csv_market_data.py --csv <PATH_TO_CSV> --pair EURUSD
```

### pytest Import Mismatch Due to Duplicate Test Filenames

**Symptom:** `ImportError` or wrong test module loaded.

**Fix:** Use unique test filenames per phase:
```bash
python3 -m pytest tests/ -q
```
Avoid duplicate names like `test_readiness.py` across multiple folders.

### __MACOSX in ZIP

**Symptom:** macOS adds `__MACOSX` folder when creating ZIP files.

**Fix:** Remove before sharing:
```bash
zip -d quant_agent_phase*.zip "__MACOSX/*" "*/.DS_Store"
```

### __pycache__ / pytest Cache

**Symptom:** Cached bytecode causes stale behavior.

**Fix:**
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name .pytest_cache -exec rm -rf {} +
rm -rf .pytest_cache
```

### Generated Outputs Accidentally Showing in git status

**Symptom:** `git status` shows `reports/`, `logs/`, `data/market/` as untracked.

**Fix:** Ensure `.gitignore` includes:
```
reports/
logs/
data/market/
data/raw_imports/
data/market_versions/
local_configs/
backups/
```

### Readiness Score Warnings

**Symptom:** Readiness audit shows warnings or low score.

**Fix:**
```bash
# Check specific areas
python3 tools/check_paper_only_safety.py --config examples/readiness_gate_config.example.json
python3 tools/check_credential_exposure.py --config examples/readiness_gate_config.example.json

# Review report
cat reports/readiness_gate/readiness_report.md
```

### Dashboard Port Already in Use

**Symptom:** `OSError: [Errno 48] Address already in use`

**Fix:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port (if supported by config)
```

### Config Path Mistakes

**Symptom:** `FileNotFoundError` for config files.

**Fix:** Use relative paths from project root:
```bash
python3 tools/run_local_workflow.py --config examples/local_app_config.example.json
```
Not:
```bash
python3 tools/run_local_workflow.py --config /absolute/path/to/config.json
```

### Paper Simulator Fills Simulated: 0

**Symptom:** Simulator shows `Fills simulated: 0`.

**Fix:** Check that paper orchestration generated decisions (not `PAPER_NEUTRAL`). Ensure strategy signals are non-neutral and risk limits allow trades.

### Exposure Warning Scaling

**Symptom:** Exposure warnings appear even with small positions.

**Fix:** Check `max_symbol_weight` and `max_gross_exposure` in `examples/paper_simulator_config.example.json`. Adjust if your test data has unusual scaling.

### Scheduler Command Review

**Symptom:** Generated cron command looks wrong.

**Fix:** The scheduler tool only prints commands. Review before manually adding to crontab:
```bash
python3 tools/generate_scheduler_command.py
# Copy and paste the output into your crontab after review
```
