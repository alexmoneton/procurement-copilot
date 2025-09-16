# Railway deployment Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install uv && uv pip install --system -e .

# Copy application code
COPY backend/ ./backend/

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port (Railway will set PORT env var)
EXPOSE $PORT

# Default command
CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
