#!/bin/bash
set -e

# Get port from environment variable, default to 8000
PORT=${PORT:-8000}

echo "Starting Procurement Copilot API on port $PORT"

# Start the FastAPI application
exec uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
