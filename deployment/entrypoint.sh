#!/bin/sh
set -e

echo "Starting Quant Platform..."
echo "Mode: ${QUANT_MODE:-paper}"

# Run migrations
python -c "
from persistence.connection import ConnectionManager
from persistence.migrations import MigrationRunner
conn = ConnectionManager(backend='sqlite')
runner = MigrationRunner(conn)
runner.apply_all()
print('Migrations applied.')
"

# Start app
exec uvicorn main:app --host 0.0.0.0 --port 8000
