# Procfile for Railway/Render deployment
web: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips '*'
worker: python -m backend.app.tasks.scheduler
migrate: python -m alembic upgrade head
