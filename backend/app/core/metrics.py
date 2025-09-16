"""Metrics collection for monitoring."""

from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..db.session import AsyncSessionLocal
from ..db.crud import TenderCRUD, EmailLogCRUD, UserCRUD
from ..core.logging import get_request_logger


class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.start_time = datetime.now()
    
    def increment(self, metric_name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        key = self._make_key(metric_name, labels)
        self.counters[key] += value
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        key = self._make_key(metric_name, labels)
        self.gauges[key] = value
    
    def observe_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Observe a histogram metric."""
        key = self._make_key(metric_name, labels)
        self.histograms[key].append(value)
    
    def _make_key(self, metric_name: str, labels: Dict[str, str] = None) -> str:
        """Create a key for metric storage."""
        if not labels:
            return metric_name
        
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{metric_name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics in Prometheus format."""
        metrics = []
        
        # Add counters
        for key, value in self.counters.items():
            metrics.append(f"# TYPE {key.split('{')[0]} counter")
            metrics.append(f"{key} {value}")
        
        # Add gauges
        for key, value in self.gauges.items():
            metrics.append(f"# TYPE {key.split('{')[0]} gauge")
            metrics.append(f"{key} {value}")
        
        # Add histograms (simplified)
        for key, values in self.histograms.items():
            if values:
                base_name = key.split('{')[0]
                metrics.append(f"# TYPE {base_name} histogram")
                metrics.append(f"{key}_count {len(values)}")
                metrics.append(f"{key}_sum {sum(values)}")
                metrics.append(f"{key}_avg {sum(values) / len(values)}")
        
        return "\n".join(metrics)


# Global metrics collector
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Collect metrics
        metrics_collector.increment(
            "http_requests_total",
            labels={
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": str(response.status_code)
            }
        )
        
        metrics_collector.observe_histogram(
            "http_request_duration_seconds",
            response_time,
            labels={
                "method": request.method,
                "endpoint": request.url.path
            }
        )
        
        return response


async def collect_database_metrics():
    """Collect database-related metrics."""
    async with AsyncSessionLocal() as db:
        try:
            # Count tenders
            tender_count = await TenderCRUD.count_tenders(db)
            metrics_collector.set_gauge("tenders_total", tender_count)
            
            # Count users
            user_count = await UserCRUD.count_users(db)
            metrics_collector.set_gauge("users_total", user_count)
            
            # Count email logs (last 24 hours)
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            email_count = await EmailLogCRUD.count_emails_since(db, yesterday)
            metrics_collector.set_gauge("emails_sent_24h", email_count)
            
        except Exception as e:
            # Log error but don't fail
            logger = get_request_logger(None, "metrics")
            logger.error(f"Failed to collect database metrics: {e}")


def increment_tender_scraped(source: str):
    """Increment tender scraped counter."""
    metrics_collector.increment(
        "tenders_scraped_total",
        labels={"source": source}
    )


def increment_alert_sent(filter_id: str, user_id: str):
    """Increment alert sent counter."""
    metrics_collector.increment(
        "alerts_sent_total",
        labels={"filter_id": filter_id, "user_id": user_id}
    )


def increment_outreach_sent(campaign_type: str, strategy: str):
    """Increment outreach sent counter."""
    metrics_collector.increment(
        "outreach_sent_total",
        labels={"campaign_type": campaign_type, "strategy": strategy}
    )


def increment_user_registered():
    """Increment user registration counter."""
    metrics_collector.increment("users_registered_total")


def increment_subscription_created(plan: str):
    """Increment subscription creation counter."""
    metrics_collector.increment(
        "subscriptions_created_total",
        labels={"plan": plan}
    )


async def start_metrics_collection():
    """Start periodic metrics collection."""
    while True:
        try:
            await collect_database_metrics()
            await asyncio.sleep(60)  # Collect every minute
        except Exception as e:
            logger = get_request_logger(None, "metrics")
            logger.error(f"Error in metrics collection: {e}")
            await asyncio.sleep(60)
