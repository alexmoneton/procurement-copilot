"""Structured logging configuration."""

import json
import sys
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class StructuredLogger:
    """Structured JSON logger."""
    
    def __init__(self):
        self.logger = logger
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure structured logging."""
        # Remove default handler
        self.logger.remove()
        
        # Add JSON formatter for production
        self.logger.add(
            sys.stdout,
            format=self._json_formatter,
            level="INFO",
            serialize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Add console formatter for development
        self.logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
    
    def _json_formatter(self, record: Dict[str, Any]) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "request_id": getattr(record["extra"], "request_id", None),
            "user_id": getattr(record["extra"], "user_id", None),
            "service": "procurement-copilot",
            "version": "0.1.0"
        }
        
        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        # Add extra fields
        for key, value in record["extra"].items():
            if key not in ["request_id", "user_id"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)
    
    def get_logger(self, name: str = None):
        """Get logger instance."""
        if name:
            return self.logger.bind(service=name)
        return self.logger


# Global logger instance
structured_logger = StructuredLogger()
app_logger = structured_logger.get_logger("app")


def get_request_logger(request: Request, name: str = None):
    """Get logger with request context."""
    logger_instance = structured_logger.get_logger(name)
    request_id = getattr(request.state, "request_id", None)
    return logger_instance.bind(request_id=request_id)


def log_request(request: Request, response_time: float, status_code: int):
    """Log HTTP request."""
    logger_instance = get_request_logger(request, "http")
    
    logger_instance.info(
        "HTTP request completed",
        method=request.method,
        url=str(request.url),
        status_code=status_code,
        response_time_ms=round(response_time * 1000, 2),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )


def log_business_event(
    event_type: str,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log business events."""
    logger_instance = structured_logger.get_logger("business")
    
    logger_instance.info(
        f"Business event: {event_type}",
        event_type=event_type,
        user_id=user_id,
        **kwargs
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """Log errors with context."""
    logger_instance = structured_logger.get_logger("error")
    
    logger_instance.error(
        f"Error occurred: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        user_id=user_id,
        context=context or {}
    )