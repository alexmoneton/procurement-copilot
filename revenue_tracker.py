#!/usr/bin/env python3
"""
Revenue Tracking System for TenderPulse
Tracks key business metrics for launch success
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

class RevenueTracker:
    def __init__(self, db_path: str = "revenue_tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize revenue tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date TEXT PRIMARY KEY,
                prospects_emailed INTEGER DEFAULT 0,
                email_opens INTEGER DEFAULT 0,
                email_responses INTEGER DEFAULT 0,
                trial_signups INTEGER DEFAULT 0,
                paid_conversions INTEGER DEFAULT 0,
                revenue_eur REAL DEFAULT 0.0,
                system_uptime_percent REAL DEFAULT 100.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_acquisitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                signup_date TEXT,
                conversion_date TEXT,
                subscription_plan TEXT,
                monthly_revenue REAL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_daily_metrics(self, date: str, metrics: Dict[str, Any]):
        """Record daily business metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_metrics 
            (date, prospects_emailed, email_opens, email_responses, 
             trial_signups, paid_conversions, revenue_eur, system_uptime_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date,
            metrics.get('prospects_emailed', 0),
            metrics.get('email_opens', 0),
            metrics.get('email_responses', 0),
            metrics.get('trial_signups', 0),
            metrics.get('paid_conversions', 0),
            metrics.get('revenue_eur', 0.0),
            metrics.get('system_uptime_percent', 100.0)
        ))
        
        conn.commit()
        conn.close()
    
    def record_customer_acquisition(self, email: str, signup_date: str, 
                                  conversion_date: str = None, 
                                  subscription_plan: str = None,
                                  monthly_revenue: float = 0.0,
                                  source: str = "organic"):
        """Record customer acquisition"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO customer_acquisitions 
            (email, signup_date, conversion_date, subscription_plan, 
             monthly_revenue, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, signup_date, conversion_date, subscription_plan, 
              monthly_revenue, source))
        
        conn.commit()
        conn.close()
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get weekly business summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last 7 days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                SUM(prospects_emailed) as total_prospects,
                SUM(email_opens) as total_opens,
                SUM(email_responses) as total_responses,
                SUM(trial_signups) as total_trials,
                SUM(paid_conversions) as total_conversions,
                SUM(revenue_eur) as total_revenue,
                AVG(system_uptime_percent) as avg_uptime
            FROM daily_metrics 
            WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        
        # Calculate conversion rates
        total_prospects = result[0] or 0
        total_opens = result[1] or 0
        total_responses = result[2] or 0
        total_trials = result[3] or 0
        total_conversions = result[4] or 0
        
        open_rate = (total_opens / total_prospects * 100) if total_prospects > 0 else 0
        response_rate = (total_responses / total_opens * 100) if total_opens > 0 else 0
        trial_rate = (total_trials / total_responses * 100) if total_responses > 0 else 0
        conversion_rate = (total_conversions / total_trials * 100) if total_trials > 0 else 0
        
        conn.close()
        
        return {
            "period": f"{start_date} to {end_date}",
            "prospects_emailed": total_prospects,
            "email_opens": total_opens,
            "email_responses": total_responses,
            "trial_signups": total_trials,
            "paid_conversions": total_conversions,
            "total_revenue_eur": result[5] or 0.0,
            "system_uptime_percent": result[6] or 100.0,
            "conversion_rates": {
                "open_rate": round(open_rate, 2),
                "response_rate": round(response_rate, 2),
                "trial_rate": round(trial_rate, 2),
                "conversion_rate": round(conversion_rate, 2)
            }
        }
    
    def get_launch_targets(self) -> Dict[str, Any]:
        """Get Week 1 launch targets"""
        return {
            "prospects_emailed_target": 350,
            "first_paying_customer": True,
            "system_uptime_target": 99.0,
            "revenue_target_eur": 29.0,  # First subscription
            "conversion_rate_target": 2.0  # 2% trial to paid
        }
    
    def check_launch_progress(self) -> Dict[str, Any]:
        """Check progress against launch targets"""
        summary = self.get_weekly_summary()
        targets = self.get_launch_targets()
        
        progress = {
            "prospects_emailed": {
                "current": summary["prospects_emailed"],
                "target": targets["prospects_emailed_target"],
                "progress_percent": round((summary["prospects_emailed"] / targets["prospects_emailed_target"]) * 100, 1)
            },
            "paying_customers": {
                "current": summary["paid_conversions"],
                "target": 1,
                "achieved": summary["paid_conversions"] >= 1
            },
            "system_uptime": {
                "current": summary["system_uptime_percent"],
                "target": targets["system_uptime_target"],
                "achieved": summary["system_uptime_percent"] >= targets["system_uptime_target"]
            },
            "revenue": {
                "current": summary["total_revenue_eur"],
                "target": targets["revenue_target_eur"],
                "progress_percent": round((summary["total_revenue_eur"] / targets["revenue_target_eur"]) * 100, 1)
            }
        }
        
        return {
            "summary": summary,
            "targets": targets,
            "progress": progress,
            "launch_success": all([
                progress["prospects_emailed"]["progress_percent"] >= 100,
                progress["paying_customers"]["achieved"],
                progress["system_uptime"]["achieved"]
            ])
        }

def main():
    tracker = RevenueTracker()
    
    # Initialize with today's metrics (zeros for now)
    today = datetime.now().strftime('%Y-%m-%d')
    tracker.record_daily_metrics(today, {
        "prospects_emailed": 0,
        "email_opens": 0,
        "email_responses": 0,
        "trial_signups": 0,
        "paid_conversions": 0,
        "revenue_eur": 0.0,
        "system_uptime_percent": 100.0
    })
    
    # Check launch progress
    progress = tracker.check_launch_progress()
    
    print("📊 REVENUE TRACKING SYSTEM INITIALIZED")
    print("="*50)
    print(f"📅 Today: {today}")
    print(f"🎯 Prospects Target: {progress['targets']['prospects_emailed_target']}")
    print(f"💰 Revenue Target: €{progress['targets']['revenue_target_eur']}")
    print(f"🚀 Launch Success: {'READY' if progress['launch_success'] else 'IN PROGRESS'}")
    print("="*50)

if __name__ == "__main__":
    main()
