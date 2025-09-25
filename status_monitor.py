#!/usr/bin/env python3
"""
Status Monitoring Panel for TenderPulse
Shadow-mode monitoring with source tracking, error rates, and deviation analysis.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SourceStats:
    source: str
    count_24h: int
    count_7d_avg: float
    deviation: float
    error_rate: float
    last_24h_errors: int
    status: str  # 'healthy', 'warning', 'critical'

@dataclass
class SystemHealth:
    overall_status: str
    sources: List[SourceStats]
    total_prospects_24h: int
    total_errors_24h: int
    system_uptime: str
    last_update: datetime

class StatusMonitor:
    """
    Status monitoring system for shadow-mode operations.
    """
    
    def __init__(self, db_path: str = "status_monitor.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize monitoring database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Source activity tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                count INTEGER NOT NULL,
                errors INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Error tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT,
                severity TEXT DEFAULT 'error',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Health checks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_name TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Status monitor database initialized")
    
    def record_source_activity(self, source: str, count: int, errors: int = 0):
        """Record daily activity for a source."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO source_activity (source, count, errors, date)
            VALUES (?, ?, ?, ?)
        """, (source, count, errors, today))
        
        conn.commit()
        conn.close()
    
    def record_error(self, source: str, error_type: str, error_message: str, severity: str = 'error'):
        """Record an error for monitoring."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO error_log (source, error_type, error_message, severity)
            VALUES (?, ?, ?, ?)
        """, (source, error_type, error_message, severity))
        
        conn.commit()
        conn.close()
    
    def get_source_stats(self, source: str) -> SourceStats:
        """Get statistics for a specific source."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 24h count
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT count, errors FROM source_activity 
            WHERE source = ? AND date >= ?
        """, (source, yesterday))
        
        last_24h_data = cursor.fetchall()
        count_24h = sum(row[0] for row in last_24h_data)
        errors_24h = sum(row[1] for row in last_24h_data)
        
        # Get 7-day average
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT count FROM source_activity 
            WHERE source = ? AND date >= ?
            ORDER BY date
        """, (source, week_ago))
        
        week_data = [row[0] for row in cursor.fetchall()]
        count_7d_avg = statistics.mean(week_data) if week_data else 0
        
        # Calculate deviation
        if count_7d_avg > 0:
            deviation = ((count_24h - count_7d_avg) / count_7d_avg) * 100
        else:
            deviation = 0
        
        # Calculate error rate
        error_rate = (errors_24h / count_24h * 100) if count_24h > 0 else 0
        
        # Determine status
        if error_rate > 10 or abs(deviation) > 50:
            status = 'critical'
        elif error_rate > 5 or abs(deviation) > 25:
            status = 'warning'
        else:
            status = 'healthy'
        
        conn.close()
        
        return SourceStats(
            source=source,
            count_24h=count_24h,
            count_7d_avg=count_7d_avg,
            deviation=deviation,
            error_rate=error_rate,
            last_24h_errors=errors_24h,
            status=status
        )
    
    def get_system_health(self) -> SystemHealth:
        """Get overall system health status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all sources
        cursor.execute("SELECT DISTINCT source FROM source_activity")
        sources = [row[0] for row in cursor.fetchall()]
        
        # Get stats for each source
        source_stats = []
        for source in sources:
            stats = self.get_source_stats(source)
            source_stats.append(stats)
        
        # Calculate totals
        total_prospects_24h = sum(stats.count_24h for stats in source_stats)
        total_errors_24h = sum(stats.last_24h_errors for stats in source_stats)
        
        # Determine overall status
        critical_sources = [s for s in source_stats if s.status == 'critical']
        warning_sources = [s for s in source_stats if s.status == 'warning']
        
        if critical_sources:
            overall_status = 'critical'
        elif warning_sources:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        # Calculate system uptime (simplified)
        cursor.execute("""
            SELECT MIN(created_at) FROM source_activity
        """)
        result = cursor.fetchone()
        if result and result[0]:
            start_time = datetime.fromisoformat(result[0])
            uptime = datetime.now() - start_time
            uptime_str = f"{uptime.days} days, {uptime.seconds // 3600} hours"
        else:
            uptime_str = "Unknown"
        
        conn.close()
        
        return SystemHealth(
            overall_status=overall_status,
            sources=source_stats,
            total_prospects_24h=total_prospects_24h,
            total_errors_24h=total_errors_24h,
            system_uptime=uptime_str,
            last_update=datetime.now()
        )
    
    def get_status_dashboard_data(self) -> Dict:
        """Get data for status dashboard."""
        health = self.get_system_health()
        
        return {
            'overall_status': health.overall_status,
            'last_update': health.last_update.isoformat(),
            'system_uptime': health.system_uptime,
            'totals': {
                'prospects_24h': health.total_prospects_24h,
                'errors_24h': health.total_errors_24h
            },
            'sources': [
                {
                    'name': source.source,
                    'count_24h': source.count_24h,
                    'count_7d_avg': round(source.count_7d_avg, 1),
                    'deviation': round(source.deviation, 1),
                    'error_rate': round(source.error_rate, 1),
                    'status': source.status
                }
                for source in health.sources
            ],
            'alerts': self._get_alerts(health)
        }
    
    def _get_alerts(self, health: SystemHealth) -> List[Dict]:
        """Get current alerts based on system health."""
        alerts = []
        
        for source in health.sources:
            if source.status == 'critical':
                alerts.append({
                    'type': 'critical',
                    'source': source.source,
                    'message': f"Critical issues detected: {source.error_rate:.1f}% error rate, {source.deviation:+.1f}% deviation"
                })
            elif source.status == 'warning':
                alerts.append({
                    'type': 'warning',
                    'source': source.source,
                    'message': f"Warning: {source.error_rate:.1f}% error rate, {source.deviation:+.1f}% deviation"
                })
        
        return alerts
    
    def run_health_checks(self) -> Dict:
        """Run comprehensive health checks."""
        checks = {}
        
        # Check database connectivity
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            checks['database'] = {'status': 'healthy', 'message': 'Database accessible'}
        except Exception as e:
            checks['database'] = {'status': 'critical', 'message': f'Database error: {e}'}
        
        # Check recent activity
        health = self.get_system_health()
        if health.total_prospects_24h == 0:
            checks['activity'] = {'status': 'warning', 'message': 'No prospects found in last 24h'}
        else:
            checks['activity'] = {'status': 'healthy', 'message': f'{health.total_prospects_24h} prospects in last 24h'}
        
        # Check error rates
        if health.total_errors_24h > health.total_prospects_24h * 0.1:
            checks['errors'] = {'status': 'critical', 'message': f'High error rate: {health.total_errors_24h} errors'}
        else:
            checks['errors'] = {'status': 'healthy', 'message': f'Low error rate: {health.total_errors_24h} errors'}
        
        return checks

def main():
    """Test the status monitoring system."""
    monitor = StatusMonitor()
    
    # Simulate some activity
    monitor.record_source_activity('ted_api', 150, 2)
    monitor.record_source_activity('apollo_io', 45, 1)
    monitor.record_source_activity('hunter_io', 30, 0)
    monitor.record_source_activity('sendgrid', 25, 1)
    
    # Record some errors
    monitor.record_error('ted_api', 'timeout', 'Request timeout after 30s', 'warning')
    monitor.record_error('apollo_io', 'rate_limit', 'Rate limit exceeded', 'error')
    
    # Get system health
    health = monitor.get_system_health()
    
    print("📊 Status Monitor Test")
    print("=" * 40)
    print(f"Overall Status: {health.overall_status.upper()}")
    print(f"System Uptime: {health.system_uptime}")
    print(f"Total Prospects (24h): {health.total_prospects_24h}")
    print(f"Total Errors (24h): {health.total_errors_24h}")
    
    print("\nSource Statistics:")
    for source in health.sources:
        print(f"  {source.source}:")
        print(f"    Count (24h): {source.count_24h}")
        print(f"    Avg (7d): {source.count_7d_avg:.1f}")
        print(f"    Deviation: {source.deviation:+.1f}%")
        print(f"    Error Rate: {source.error_rate:.1f}%")
        print(f"    Status: {source.status}")
    
    # Get dashboard data
    dashboard_data = monitor.get_status_dashboard_data()
    print(f"\nDashboard Data: {json.dumps(dashboard_data, indent=2)}")
    
    # Run health checks
    checks = monitor.run_health_checks()
    print(f"\nHealth Checks:")
    for check_name, result in checks.items():
        print(f"  {check_name}: {result['status']} - {result['message']}")
    
    print("\n✅ Status monitoring system working!")

if __name__ == "__main__":
    main()
