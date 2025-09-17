#!/bin/bash
set -e

# Get port from environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting Procurement Copilot API on port $PORT"
echo "Environment variables:"
env | grep -E "(PORT|DATABASE|DB_)" || echo "No DB vars found"

echo "Testing if we can import the main app..."
if python3 -c "from backend.app.main import app; print('Main app import successful')" 2>&1; then
    echo "Main app imports successfully, starting full app..."
    exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
else
    echo "Main app import failed, starting minimal app..."
    exec python3 minimal_app.py
fi
