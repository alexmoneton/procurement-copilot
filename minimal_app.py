#!/usr/bin/env python3
"""
Minimal FastAPI app for debugging Railway deployment issues.
"""

import os
import sys

print("=" * 50)
print("MINIMAL APP STARTING")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
print("All environment variables:")
for key, value in os.environ.items():
    if any(x in key.upper() for x in ['PORT', 'DATABASE', 'DB_', 'RAILWAY']):
        print(f"  {key}={value}")
print("=" * 50)

try:
    from fastapi import FastAPI
    print("FastAPI import successful")
except Exception as e:
    print(f"FastAPI import failed: {e}")
    sys.exit(1)

app = FastAPI(title="Minimal Procurement Copilot")

@app.get("/")
async def root():
    return {"message": "Minimal API is running", "port": os.environ.get("PORT", "unknown")}

@app.get("/ping")
async def ping():
    print("Ping endpoint called")
    return "pong"

@app.get("/health")
async def health():
    print("Health endpoint called")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
