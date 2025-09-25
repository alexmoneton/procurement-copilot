#!/usr/bin/env python3
"""
Funnel Telemetry System for TenderPulse
Comprehensive event tracking for cohort analysis and funnel optimization.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    LEAD_FOUND = "lead_found"
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    EMAIL_REPLIED = "email_replied"
    TRIAL_STARTED = "trial_started"
    PAID = "paid"
    CHURNED = "churned"
    PROFILE_CREATED = "profile_created"
    TENDER_VIEWED = "tender_viewed"
    TENDER_SAVED = "tender_saved"
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_SENT = "campaign_sent"

class EntityType(Enum):
    PROSPECT = "prospect"
    USER = "user"
    TENDER = "tender"
    CAMPAIGN = "campaign"
    EMAIL = "email"

@dataclass
class FunnelEvent:
    event_type: EventType
    entity_type: EntityType
    entity_id: str
    properties: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class CohortData:
    cohort_date: str
    total_users: int
    events: Dict[str, int]
    conversion_rates: Dict[str, float]

class FunnelTelemetry:
    """
    Comprehensive funnel telemetry system for tracking user journey and conversions.
    """
    
    def __init__(self, db_path: str = "funnel_telemetry.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize telemetry database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                properties TEXT
            )
        """)
        
        # Cohort tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cohorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cohort_date TEXT NOT NULL,
                user_id TEXT NOT NULL,
                first_event TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cohort_date, user_id)
            )
        """)
        
        # Funnel steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funnel_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_name TEXT NOT NULL,
                step_order INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_type, entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cohorts_date ON cohorts(cohort_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cohorts_user ON cohorts(user_id)")
        
        # Insert default funnel steps
        default_steps = [
            ("lead_found", 1, "lead_found"),
            ("email_sent", 2, "email_sent"),
            ("email_opened", 3, "email_opened"),
            ("email_replied", 4, "email_replied"),
            ("trial_started", 5, "trial_started"),
            ("paid", 6, "paid")
        ]
        
        for step_name, step_order, event_type in default_steps:
            cursor.execute("""
                INSERT OR IGNORE INTO funnel_steps (step_name, step_order, event_type)
                VALUES (?, ?, ?)
            """, (step_name, step_order, event_type))
        
        conn.commit()
        conn.close()
        logger.info("Funnel telemetry database initialized")
    
    def track_event(
        self,
        event_type: EventType,
        entity_type: EntityType,
        entity_id: str,
        properties: Dict[str, Any] = None,
        user_id: str = None,
        session_id: str = None
    ):
        """Track a funnel event."""
        if properties is None:
            properties = {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (event_type, entity_type, entity_id, user_id, session_id, properties)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_type.value,
            entity_type.value,
            entity_id,
            user_id,
            session_id,
            json.dumps(properties)
        ))
        
        # Update cohort if this is a new user
        if user_id and event_type == EventType.LEAD_FOUND:
            self._update_cohort(user_id, event_type.value)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tracked event: {event_type.value} for {entity_type.value}:{entity_id}")
    
    def _update_cohort(self, user_id: str, first_event: str):
        """Update user cohort information."""
        cohort_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO cohorts (cohort_date, user_id, first_event)
            VALUES (?, ?, ?)
        """, (cohort_date, user_id, first_event))
        
        conn.commit()
        conn.close()
    
    def get_funnel_metrics(self, days: int = 30) -> Dict:
        """Get funnel conversion metrics."""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get funnel steps
        cursor.execute("SELECT step_name, step_order, event_type FROM funnel_steps ORDER BY step_order")
        steps = cursor.fetchall()
        
        funnel_data = {}
        
        for step_name, step_order, event_type in steps:
            # Count events for this step
            cursor.execute("""
                SELECT COUNT(DISTINCT entity_id) FROM events 
                WHERE event_type = ? AND created_at >= ?
            """, (event_type, start_date))
            
            count = cursor.fetchone()[0]
            funnel_data[step_name] = {
                'step_order': step_order,
                'count': count,
                'event_type': event_type
            }
        
        # Calculate conversion rates
        if funnel_data:
            base_count = funnel_data.get('lead_found', {}).get('count', 0)
            if base_count > 0:
                for step_name, data in funnel_data.items():
                    conversion_rate = (data['count'] / base_count) * 100
                    data['conversion_rate'] = round(conversion_rate, 2)
            else:
                for step_name, data in funnel_data.items():
                    data['conversion_rate'] = 0
        
        conn.close()
        return funnel_data
    
    def get_cohort_analysis(self, cohort_days: int = 30) -> List[CohortData]:
        """Get cohort analysis data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get cohort dates
        cursor.execute("""
            SELECT DISTINCT cohort_date FROM cohorts 
            WHERE cohort_date >= date('now', '-{} days')
            ORDER BY cohort_date
        """.format(cohort_days))
        
        cohort_dates = [row[0] for row in cursor.fetchall()]
        cohort_data = []
        
        for cohort_date in cohort_dates:
            # Get users in this cohort
            cursor.execute("""
                SELECT user_id FROM cohorts WHERE cohort_date = ?
            """, (cohort_date,))
            
            cohort_users = [row[0] for row in cursor.fetchall()]
            total_users = len(cohort_users)
            
            # Get events for this cohort
            events = {}
            for event_type in EventType:
                cursor.execute("""
                    SELECT COUNT(*) FROM events 
                    WHERE user_id IN ({}) AND event_type = ?
                """.format(','.join(['?' for _ in cohort_users])), 
                cohort_users + [event_type.value])
                
                count = cursor.fetchone()[0]
                events[event_type.value] = count
            
            # Calculate conversion rates
            conversion_rates = {}
            if total_users > 0:
                for event_type, count in events.items():
                    conversion_rates[event_type] = round((count / total_users) * 100, 2)
            
            cohort_data.append(CohortData(
                cohort_date=cohort_date,
                total_users=total_users,
                events=events,
                conversion_rates=conversion_rates
            ))
        
        conn.close()
        return cohort_data
    
    def get_user_journey(self, user_id: str) -> List[Dict]:
        """Get complete user journey."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, entity_type, entity_id, properties, created_at
            FROM events 
            WHERE user_id = ? 
            ORDER BY created_at
        """, (user_id,))
        
        journey = []
        for row in cursor.fetchall():
            event_type, entity_type, entity_id, properties_json, created_at = row
            properties = json.loads(properties_json) if properties_json else {}
            
            journey.append({
                'event_type': event_type,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'properties': properties,
                'timestamp': created_at
            })
        
        conn.close()
        return journey
    
    def get_daily_metrics(self, days: int = 30) -> Dict:
        """Get daily metrics for dashboard."""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily event counts
        cursor.execute("""
            SELECT DATE(created_at) as date, event_type, COUNT(*) as count
            FROM events 
            WHERE created_at >= ?
            GROUP BY DATE(created_at), event_type
            ORDER BY date
        """, (start_date,))
        
        daily_data = {}
        for row in cursor.fetchall():
            date, event_type, count = row
            if date not in daily_data:
                daily_data[date] = {}
            daily_data[date][event_type] = count
        
        # Total metrics
        cursor.execute("""
            SELECT event_type, COUNT(*) as total
            FROM events 
            WHERE created_at >= ?
            GROUP BY event_type
        """, (start_date,))
        
        totals = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'daily_data': daily_data,
            'totals': totals,
            'period_days': days
        }
    
    def get_conversion_funnel(self) -> Dict:
        """Get conversion funnel visualization data."""
        funnel_metrics = self.get_funnel_metrics()
        
        # Calculate drop-off rates
        steps = list(funnel_metrics.keys())
        drop_offs = {}
        
        for i, step in enumerate(steps):
            if i == 0:
                drop_offs[step] = 0
            else:
                prev_step = steps[i-1]
                prev_count = funnel_metrics[prev_step]['count']
                current_count = funnel_metrics[step]['count']
                
                if prev_count > 0:
                    drop_off = ((prev_count - current_count) / prev_count) * 100
                    drop_offs[step] = round(drop_off, 2)
                else:
                    drop_offs[step] = 0
        
        return {
            'steps': funnel_metrics,
            'drop_offs': drop_offs
        }

def main():
    """Test the funnel telemetry system."""
    telemetry = FunnelTelemetry()
    
    # Simulate some events
    telemetry.track_event(
        EventType.LEAD_FOUND,
        EntityType.PROSPECT,
        "prospect_123",
        {"company": "TechCorp", "country": "DE"},
        user_id="user_456"
    )
    
    telemetry.track_event(
        EventType.EMAIL_SENT,
        EntityType.EMAIL,
        "email_789",
        {"campaign": "initial_outreach"},
        user_id="user_456"
    )
    
    telemetry.track_event(
        EventType.EMAIL_OPENED,
        EntityType.EMAIL,
        "email_789",
        {"opened_at": datetime.now().isoformat()},
        user_id="user_456"
    )
    
    telemetry.track_event(
        EventType.TRIAL_STARTED,
        EntityType.USER,
        "user_456",
        {"plan": "free_trial"},
        user_id="user_456"
    )
    
    # Get metrics
    print("📊 Funnel Telemetry Test")
    print("=" * 40)
    
    funnel_metrics = telemetry.get_funnel_metrics()
    print("Funnel Metrics:")
    for step, data in funnel_metrics.items():
        print(f"  {step}: {data['count']} ({data.get('conversion_rate', 0)}%)")
    
    conversion_funnel = telemetry.get_conversion_funnel()
    print(f"\nConversion Funnel: {json.dumps(conversion_funnel, indent=2)}")
    
    daily_metrics = telemetry.get_daily_metrics()
    print(f"\nDaily Metrics: {json.dumps(daily_metrics, indent=2)}")
    
    user_journey = telemetry.get_user_journey("user_456")
    print(f"\nUser Journey: {json.dumps(user_journey, indent=2)}")
    
    print("\n✅ Funnel telemetry system working!")

if __name__ == "__main__":
    main()
