#!/usr/bin/env python3
"""
Cost Guardrails System for TenderPulse
Prevents API quota exhaustion with daily budgets, caching, and relevance scoring.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DailyBudget:
    apollo_requests: int
    hunter_requests: int
    sendgrid_emails: int
    ted_requests: int

@dataclass
class UsageStats:
    apollo_used: int
    hunter_used: int
    sendgrid_used: int
    ted_used: int
    date: str

class CostGuardrails:
    """
    Cost guardrails system to prevent API quota exhaustion.
    """
    
    def __init__(self, config_path: str = "config.json", db_path: str = "cost_guardrails.db"):
        self.config = self._load_config(config_path)
        self.db_path = db_path
        self.daily_budgets = self._load_daily_budgets()
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 24)
        
        # Initialize database
        self._init_database()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            return {}
    
    def _load_daily_budgets(self) -> DailyBudget:
        """Load daily budgets from config."""
        budgets = self.config.get('daily_budgets', {})
        return DailyBudget(
            apollo_requests=budgets.get('apollo_requests', 1000),
            hunter_requests=budgets.get('hunter_requests', 500),
            sendgrid_emails=budgets.get('sendgrid_emails', 200),
            ted_requests=budgets.get('ted_requests', 2000)
        )
    
    def _init_database(self):
        """Initialize SQLite database for tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Usage tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                apollo_used INTEGER DEFAULT 0,
                hunter_used INTEGER DEFAULT 0,
                sendgrid_used INTEGER DEFAULT 0,
                ted_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        """)
        
        # Email cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                email TEXT,
                confidence_score INTEGER,
                source TEXT,
                ttl_expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(domain)
            )
        """)
        
        # Relevance scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relevance_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id TEXT NOT NULL,
                score REAL NOT NULL,
                factors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(prospect_id)
            )
        """)
        
        # API call log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                endpoint TEXT,
                cost INTEGER DEFAULT 1,
                success BOOLEAN,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Cost guardrails database initialized")
    
    def get_today_usage(self) -> UsageStats:
        """Get today's API usage."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT apollo_used, hunter_used, sendgrid_used, ted_used 
            FROM daily_usage WHERE date = ?
        """, (today,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return UsageStats(
                apollo_used=result[0],
                hunter_used=result[1],
                sendgrid_used=result[2],
                ted_used=result[3],
                date=today
            )
        else:
            return UsageStats(0, 0, 0, 0, today)
    
    def can_make_request(self, provider: str) -> Tuple[bool, str]:
        """Check if we can make a request to the provider."""
        usage = self.get_today_usage()
        
        if provider == 'apollo':
            if usage.apollo_used >= self.daily_budgets.apollo_requests:
                return False, f"Apollo daily limit reached ({usage.apollo_used}/{self.daily_budgets.apollo_requests})"
        elif provider == 'hunter':
            if usage.hunter_used >= self.daily_budgets.hunter_requests:
                return False, f"Hunter daily limit reached ({usage.hunter_used}/{self.daily_budgets.hunter_requests})"
        elif provider == 'sendgrid':
            if usage.sendgrid_used >= self.daily_budgets.sendgrid_emails:
                return False, f"SendGrid daily limit reached ({usage.sendgrid_used}/{self.daily_budgets.sendgrid_emails})"
        elif provider == 'ted':
            if usage.ted_used >= self.daily_budgets.ted_requests:
                return False, f"TED daily limit reached ({usage.ted_used}/{self.daily_budgets.ted_requests})"
        
        return True, "OK"
    
    def record_api_call(self, provider: str, endpoint: str = None, success: bool = True, error_message: str = None):
        """Record an API call for usage tracking."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert API call log
        cursor.execute("""
            INSERT INTO api_calls (provider, endpoint, success, error_message)
            VALUES (?, ?, ?, ?)
        """, (provider, endpoint, success, error_message))
        
        # Update daily usage
        cursor.execute("""
            INSERT OR REPLACE INTO daily_usage (date, apollo_used, hunter_used, sendgrid_used, ted_used)
            VALUES (
                ?,
                COALESCE((SELECT apollo_used FROM daily_usage WHERE date = ?), 0) + ?,
                COALESCE((SELECT hunter_used FROM daily_usage WHERE date = ?), 0) + ?,
                COALESCE((SELECT sendgrid_used FROM daily_usage WHERE date = ?), 0) + ?,
                COALESCE((SELECT ted_used FROM daily_usage WHERE date = ?), 0) + ?
            )
        """, (
            today, today, 1 if provider == 'apollo' else 0,
            today, 1 if provider == 'hunter' else 0,
            today, 1 if provider == 'sendgrid' else 0,
            today, 1 if provider == 'ted' else 0
        ))
        
        conn.commit()
        conn.close()
    
    def get_cached_email(self, domain: str) -> Optional[Dict]:
        """Get cached email for domain if not expired."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email, confidence_score, source 
            FROM email_cache 
            WHERE domain = ? AND ttl_expires_at > ?
        """, (domain, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'email': result[0],
                'confidence_score': result[1],
                'source': result[2]
            }
        return None
    
    def cache_email(self, domain: str, email: str, confidence_score: int, source: str):
        """Cache email result with TTL."""
        ttl_expires = datetime.now() + timedelta(hours=self.cache_ttl_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO email_cache (domain, email, confidence_score, source, ttl_expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (domain, email, confidence_score, source, ttl_expires))
        
        conn.commit()
        conn.close()
    
    def calculate_relevance_score(self, prospect: Dict) -> float:
        """Calculate relevance score for prospect before enrichment."""
        score = 0.0
        
        # Company name quality (0-20 points)
        company_name = prospect.get('company_name', '')
        if company_name and len(company_name) > 3:
            score += 20
        
        # Domain presence (0-15 points)
        domain = prospect.get('domain', '')
        if domain and '.' in domain:
            score += 15
        
        # Tender value (0-25 points)
        tender_value = prospect.get('lost_tender_value', 0)
        if tender_value:
            if tender_value >= 1000000:  # 1M+
                score += 25
            elif tender_value >= 500000:  # 500K+
                score += 20
            elif tender_value >= 100000:  # 100K+
                score += 15
            else:
                score += 10
        
        # Country preference (0-15 points)
        country = prospect.get('country', '')
        preferred_countries = self.config.get('search_params', {}).get('countries', [])
        if country in preferred_countries:
            score += 15
        
        # CPV code relevance (0-25 points)
        cpv_codes = prospect.get('cpv_codes', '')
        if cpv_codes:
            # Check if CPV matches high-value sectors
            high_value_cpvs = ['72', '73', '79', '71', '45']  # IT, R&D, Business, Engineering, Construction
            cpv_family = str(cpv_codes)[:2] if len(str(cpv_codes)) >= 2 else ''
            if cpv_family in high_value_cpvs:
                score += 25
            else:
                score += 15
        
        return min(score, 100.0)  # Cap at 100
    
    def should_enrich_prospect(self, prospect: Dict, min_score: float = 60.0) -> Tuple[bool, float]:
        """Determine if prospect should be enriched based on relevance score."""
        score = self.calculate_relevance_score(prospect)
        
        # Cache the score
        prospect_id = f"{prospect.get('company_name', '')}:{prospect.get('country', '')}"
        self._cache_relevance_score(prospect_id, score)
        
        return score >= min_score, score
    
    def _cache_relevance_score(self, prospect_id: str, score: float):
        """Cache relevance score for prospect."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO relevance_scores (prospect_id, score, factors)
            VALUES (?, ?, ?)
        """, (prospect_id, score, json.dumps({'calculated_at': datetime.now().isoformat()})))
        
        conn.commit()
        conn.close()
    
    def get_usage_report(self) -> Dict:
        """Get comprehensive usage report."""
        usage = self.get_today_usage()
        
        return {
            'date': usage.date,
            'budgets': {
                'apollo_requests': self.daily_budgets.apollo_requests,
                'hunter_requests': self.daily_budgets.hunter_requests,
                'sendgrid_emails': self.daily_budgets.sendgrid_emails,
                'ted_requests': self.daily_budgets.ted_requests
            },
            'used': {
                'apollo_requests': usage.apollo_used,
                'hunter_requests': usage.hunter_used,
                'sendgrid_emails': usage.sendgrid_used,
                'ted_requests': usage.ted_used
            },
            'remaining': {
                'apollo_requests': max(0, self.daily_budgets.apollo_requests - usage.apollo_used),
                'hunter_requests': max(0, self.daily_budgets.hunter_requests - usage.hunter_used),
                'sendgrid_emails': max(0, self.daily_budgets.sendgrid_emails - usage.sendgrid_used),
                'ted_requests': max(0, self.daily_budgets.ted_requests - usage.ted_used)
            },
            'utilization': {
                'apollo_requests': f"{(usage.apollo_used / self.daily_budgets.apollo_requests * 100):.1f}%",
                'hunter_requests': f"{(usage.hunter_used / self.daily_budgets.hunter_requests * 100):.1f}%",
                'sendgrid_emails': f"{(usage.sendgrid_used / self.daily_budgets.sendgrid_emails * 100):.1f}%",
                'ted_requests': f"{(usage.ted_used / self.daily_budgets.ted_requests * 100):.1f}%"
            }
        }
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean email cache
        cursor.execute("DELETE FROM email_cache WHERE ttl_expires_at < ?", (datetime.now(),))
        email_deleted = cursor.rowcount
        
        # Clean old API calls (keep last 30 days)
        cursor.execute("DELETE FROM api_calls WHERE created_at < ?", 
                      (datetime.now() - timedelta(days=30),))
        api_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {email_deleted} expired email cache entries and {api_deleted} old API calls")

def main():
    """Test the cost guardrails system."""
    guardrails = CostGuardrails()
    
    # Test usage tracking
    print("📊 Cost Guardrails System Test")
    print("=" * 40)
    
    # Check current usage
    report = guardrails.get_usage_report()
    print(f"Today's Usage Report:")
    for provider, usage in report['used'].items():
        budget = report['budgets'][provider]
        remaining = report['remaining'][provider]
        utilization = report['utilization'][provider]
        print(f"  {provider}: {usage}/{budget} ({utilization}) - {remaining} remaining")
    
    # Test prospect relevance
    test_prospect = {
        'company_name': 'TechCorp GmbH',
        'domain': 'techcorp.de',
        'country': 'DE',
        'lost_tender_value': 1500000,
        'cpv_codes': '72000000'
    }
    
    should_enrich, score = guardrails.should_enrich_prospect(test_prospect)
    print(f"\nProspect Relevance Test:")
    print(f"  Company: {test_prospect['company_name']}")
    print(f"  Score: {score:.1f}/100")
    print(f"  Should enrich: {should_enrich}")
    
    # Test API limits
    can_apollo, msg = guardrails.can_make_request('apollo')
    print(f"\nAPI Limit Test:")
    print(f"  Can make Apollo request: {can_apollo} - {msg}")
    
    print("\n✅ Cost guardrails system working!")

if __name__ == "__main__":
    main()
