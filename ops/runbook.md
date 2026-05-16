
# Operations Runbook

## Start Paper System
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Run Tests
```bash
python -m pytest tests/ -v
```

## Check Dashboard
Open http://localhost:8000/dashboard/

## Check Audit Log
```bash
tail -f data/audit.jsonl
```

## Reset Paper Account
```bash
python tools/reset_paper_account.py
```

## Backup Data
```bash
python tools/backup_data.py --output backups/
```
