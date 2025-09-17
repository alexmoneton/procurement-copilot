#!/usr/bin/env python3
"""
Minimal FastAPI app for debugging Railway deployment issues.
"""

from fastapi import FastAPI
import os

app = FastAPI(title="Minimal Procurement Copilot")

@app.get("/")
async def root():
    return {"message": "Minimal API is running", "port": os.environ.get("PORT", "unknown")}

@app.get("/ping")
async def ping():
    return "pong"

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
