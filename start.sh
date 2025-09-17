#!/bin/bash
set -e

# Get port from environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting Procurement Copilot API on port $PORT"
echo "Environment variables:"
env | grep -E "(PORT|DATABASE|DB_)" || echo "No DB vars found"

# Start the FastAPI application with more verbose logging
exec uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --log-level info
