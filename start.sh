#!/bin/bash

# TenderPulse Production Start Script
set -e

echo "🚀 Starting TenderPulse API..."

# Wait for database
echo "⏳ Waiting for database connection..."
python -c "
import os
import time
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ DATABASE_URL not set')
    exit(1)

result = urlparse(db_url)
for i in range(30):
    try:
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        conn.close()
        print('✅ Database connected')
        break
    except:
        print(f'⏳ Database not ready, retrying... ({i+1}/30)')
        time.sleep(2)
else:
    print('❌ Database connection failed')
    exit(1)
"

# Run migrations
echo "🔄 Running database migrations..."
python -m alembic upgrade head

# Start scheduler in background if ENABLE_SCHEDULER=true
if [ "$ENABLE_SCHEDULER" = "true" ]; then
    echo "⏰ Starting background scheduler..."
    python -m backend.app.tasks.scheduler &
fi

# Start API server
echo "🌐 Starting API server on port ${PORT:-8000}..."
exec python -m uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --proxy-headers \
    --forwarded-allow-ips '*' \
    --access-log