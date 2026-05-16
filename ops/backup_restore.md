
# Backup and Restore

## Backup SQLite
```bash
cp data/quant_platform.db backups/quant_platform_$(date +%Y%m%d).db
```

## Backup Reports
```bash
cp -r reports/ backups/reports_$(date +%Y%m%d)/
```

## Backup Audit Log
```bash
cp data/audit.jsonl backups/audit_$(date +%Y%m%d).jsonl
```

## Restore
```bash
cp backups/quant_platform_YYYYMMDD.db data/quant_platform.db
```

## Verify Audit Chain
```bash
python tools/verify_audit_log.py
```
