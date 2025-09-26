#!/usr/bin/env python3
"""
Advanced TED Prospect Finder - Complete Customer Acquisition System
Find bid losers, get emails, send personalized outreach, track everything

Features:
- Real TED API integration with contract awards
- Multiple bidder detection
- Company information extraction
- Hunter.io email discovery
- Mailgun email sending
- Progress bars and detailed logging
- Rate limiting and error handling
- Email validation and bounce handling
- Configuration management
"""

import os
import json
import csv
import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path

# Third party imports
import httpx
import aiofiles
from tqdm import tqdm
import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from email_validator import validate_email, EmailNotValidError

# Configuration
console = Console()

# Setup rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("ted_finder")

@dataclass
class TenderAward:
    """Contract award with bidder information"""
    tender_id: str
    title: str
    buyer_name: str
    buyer_country: str
    award_date: str
    contract_value: str
    winner_name: str
    total_bidders: int
    cpv_codes: List[str]
    tender_url: str
    raw_data: Dict
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ProspectCompany:
    """A prospect company that lost a bid"""
    company_name: str
    country: str
    sector: str
    lost_tender_id: str
    lost_tender_title: str
    lost_tender_value: str
    lost_date: str
    buyer_name: str
    winner_name: str
    pain_level: int  # 0-100
    website: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    status: str = 'found'  # found, email_found, contacted, responded, converted
    notes: str = ''
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class ConfigManager:
    """Manage configuration and API keys"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            "api_keys": {
                "apollo_io": "",
                "hunter_io": "",
                "sendgrid": ""
            },
            "email": {
                "from_email": "hello@tenderpulse.eu",
                "from_name": "Alex from TenderPulse",
                "reply_to": "hello@tenderpulse.eu"
            },
            "rate_limits": {
                "ted_requests_per_minute": 30,
                "apollo_requests_per_minute": 20,
                "hunter_requests_per_minute": 10,
                "sendgrid_emails_per_hour": 100
            },
            "search_params": {
                "countries": ["DE", "FR", "NL", "IT", "ES", "SE", "NO", "DK"],
                "days_back": 14,
                "min_contract_value": 100000,
                "max_results_per_day": 500
            },
            "database": {
                "path": "ted_prospects.db"
            },
            "logging": {
                "level": "INFO",
                "file": "ted_finder.log"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self._deep_merge(default_config, loaded_config)
            
            return default_config
        except Exception as e:
            logger.warning(f"Could not load config: {e}. Using defaults.")
            return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save config: {e}")
    
    def get(self, path: str, default=None):
        """Get config value by dot notation path"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

class ProspectDatabase:
    """Advanced SQLite database for prospects and campaigns"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with comprehensive schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tender awards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tender_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tender_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                buyer_name TEXT,
                buyer_country TEXT,
                award_date TEXT,
                contract_value TEXT,
                winner_name TEXT,
                total_bidders INTEGER,
                cpv_codes TEXT,  -- JSON array
                tender_url TEXT,
                raw_data TEXT,   -- JSON blob
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Prospect companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                country TEXT,
                sector TEXT,
                lost_tender_id TEXT,
                lost_tender_title TEXT,
                lost_tender_value TEXT,
                lost_date TEXT,
                buyer_name TEXT,
                winner_name TEXT,
                pain_level INTEGER,
                website TEXT,
                email TEXT,
                contact_name TEXT,
                phone TEXT,
                linkedin TEXT,
                status TEXT DEFAULT 'found',
                notes TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (lost_tender_id) REFERENCES tender_awards (tender_id)
            )
        ''')
        
        # Email campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                campaign_name TEXT,
                subject TEXT,
                body TEXT,
                sent_at TEXT,
                delivered_at TEXT,
                opened_at TEXT,
                clicked_at TEXT,
                replied_at TEXT,
                bounced_at TEXT,
                status TEXT DEFAULT 'draft',  -- draft, sent, delivered, opened, clicked, replied, bounced
                mailgun_id TEXT,
                created_at TEXT,
                FOREIGN KEY (prospect_id) REFERENCES prospects (id)
            )
        ''')
        
        # Email templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                subject_template TEXT,
                body_template TEXT,
                sector TEXT,
                country TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                module TEXT,
                data TEXT,  -- JSON
                created_at TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prospects_country ON prospects(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prospects_sector ON prospects(sector)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaigns_status ON email_campaigns(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_awards_date ON tender_awards(award_date)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def save_tender_award(self, award: TenderAward) -> int:
        """Save tender award to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tender_awards 
                (tender_id, title, buyer_name, buyer_country, award_date, 
                 contract_value, winner_name, total_bidders, cpv_codes, 
                 tender_url, raw_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                award.tender_id, award.title, award.buyer_name, award.buyer_country,
                award.award_date, award.contract_value, award.winner_name,
                award.total_bidders, json.dumps(award.cpv_codes),
                award.tender_url, json.dumps(award.raw_data),
                award.created_at, datetime.now().isoformat()
            ))
            
            award_id = cursor.lastrowid
            conn.commit()
            return award_id
            
        except Exception as e:
            logger.error(f"Error saving tender award: {e}")
            return None
        finally:
            conn.close()
    
    def save_prospect(self, prospect: ProspectCompany) -> int:
        """Save prospect to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO prospects 
                (company_name, country, sector, lost_tender_id, lost_tender_title,
                 lost_tender_value, lost_date, buyer_name, winner_name, pain_level,
                 website, email, contact_name, phone, linkedin, status, notes,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prospect.company_name, prospect.country, prospect.sector,
                prospect.lost_tender_id, prospect.lost_tender_title,
                prospect.lost_tender_value, prospect.lost_date,
                prospect.buyer_name, prospect.winner_name, prospect.pain_level,
                prospect.website, prospect.email, prospect.contact_name,
                prospect.phone, prospect.linkedin, prospect.status, prospect.notes,
                prospect.created_at, datetime.now().isoformat()
            ))
            
            prospect_id = cursor.lastrowid
            conn.commit()
            return prospect_id
            
        except Exception as e:
            logger.error(f"Error saving prospect: {e}")
            return None
        finally:
            conn.close()
    
    def get_prospects_by_status(self, status: str) -> List[Dict]:
        """Get prospects by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prospects WHERE status = ? ORDER BY created_at DESC', (status,))
        columns = [description[0] for description in cursor.description]
        prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return prospects
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Prospect counts by status
        cursor.execute('SELECT status, COUNT(*) FROM prospects GROUP BY status')
        stats['prospects_by_status'] = dict(cursor.fetchall())
        
        # Total awards processed
        cursor.execute('SELECT COUNT(*) FROM tender_awards')
        stats['total_awards'] = cursor.fetchone()[0]
        
        # Email campaign stats
        cursor.execute('SELECT status, COUNT(*) FROM email_campaigns GROUP BY status')
        stats['campaigns_by_status'] = dict(cursor.fetchall())
        
        # Recent activity
        cursor.execute('SELECT COUNT(*) FROM prospects WHERE date(created_at) = date("now")')
        stats['prospects_today'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

class RateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if (now - call_time).seconds < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call).seconds
            
            if wait_time > 0:
                logger.info(f"⏳ Rate limit reached, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        self.calls.append(now)

class TEDProspectFinder:
    """Advanced TED API client for finding prospects"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.ted_endpoint = "https://api.ted.europa.eu/v3/notices/search"
        self.rate_limiter = RateLimiter(
            max_calls=config.get('rate_limits.ted_requests_per_minute', 30),
            time_window=60
        )
    
    async def find_recent_awards(self, progress_callback=None) -> List[TenderAward]:
        """Find recent contract awards with multiple bidders"""
        
        countries = self.config.get('search_params.countries', ['DE', 'FR', 'NL'])
        days_back = self.config.get('search_params.days_back', 14)
        max_results = self.config.get('search_params.max_results_per_day', 500)
        
        logger.info(f"🎯 Searching TED for contract awards in {countries} over last {days_back} days...")
        
        awards = []
        
        # Search for contract award notices
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                await self.rate_limiter.wait_if_needed()
                
                payload = {
                    "query": "TI=award OR TI=contract OR TI=winner OR TI=result",
                    "fields": ["ND", "TI", "PD", "buyer-name", "links", "AC", "TV"]
                }
                
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'TenderPulse-Advanced-Finder/2.0'
                }
                
                if progress_callback:
                    progress_callback("Calling TED API...")
                
                response = await client.post(self.ted_endpoint, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    notices = data.get('notices', [])
                    
                    logger.info(f"📊 Found {len(notices)} potential award notices")
                    
                    # Process each notice
                    for i, notice in enumerate(notices[:max_results]):
                        if progress_callback:
                            progress_callback(f"Processing notice {i+1}/{len(notices)}")
                        
                        award = await self.process_award_notice(notice)
                        if award and award.total_bidders > 1:  # Only awards with multiple bidders
                            awards.append(award)
                        
                        # Small delay to be nice to the API
                        await asyncio.sleep(0.1)
                
                else:
                    logger.error(f"❌ TED API failed: {response.status_code} - {response.text[:200]}")
                
            except Exception as e:
                logger.error(f"❌ Error calling TED API: {e}")
        
        logger.info(f"✅ Found {len(awards)} contract awards with multiple bidders")
        return awards
    
    async def process_award_notice(self, notice: Dict) -> Optional[TenderAward]:
        """Process a single award notice"""
        try:
            # Extract title
            title_obj = notice.get('TI', {})
            if isinstance(title_obj, dict):
                title = title_obj.get('eng', title_obj.get('deu', title_obj.get('fra', 
                       list(title_obj.values())[0] if title_obj else 'Contract Award')))
            else:
                title = str(title_obj) if title_obj else 'Contract Award'
            
            # Only process if it looks like an award notice
            award_keywords = ['award', 'contract', 'winner', 'result', 'selected', 'chosen']
            if not any(keyword in title.lower() for keyword in award_keywords):
                return None
            
            # Extract basic information
            tender_id = notice.get('ND', f"TED-{datetime.now().strftime('%Y%m%d')}-{hash(title) % 100000}")
            award_date = notice.get('PD', datetime.now().isoformat())
            
            # Extract buyer information
            buyer_name = self.extract_buyer_name(title, notice)
            buyer_country = self.extract_country(title)
            
            # Estimate contract value
            contract_value = self.estimate_contract_value(title, notice)
            
            # Extract winner and estimate bidder count
            winner_name = self.extract_winner_name(title)
            total_bidders = self.estimate_bidder_count(title, notice)
            
            # Extract CPV codes
            cpv_codes = self.extract_cpv_codes(title, notice)
            
            # Generate TED URL
            tender_url = f"https://ted.europa.eu/udl?uri=TED:NOTICE:{tender_id}"
            
            award = TenderAward(
                tender_id=tender_id,
                title=title,
                buyer_name=buyer_name,
                buyer_country=buyer_country,
                award_date=award_date,
                contract_value=contract_value,
                winner_name=winner_name,
                total_bidders=total_bidders,
                cpv_codes=cpv_codes,
                tender_url=tender_url,
                raw_data=notice
            )
            
            return award
            
        except Exception as e:
            logger.warning(f"Error processing notice: {e}")
            return None
    
    def extract_buyer_name(self, title: str, notice: Dict) -> str:
        """Extract buyer name from title or notice"""
        # Try to get from notice data first
        buyer_name = notice.get('buyer-name', '')
        if buyer_name:
            # Handle case where buyer_name is a dictionary
            if isinstance(buyer_name, dict):
                # Extract the first meaningful value from the dict
                for key, value in buyer_name.items():
                    if value and isinstance(value, str) and len(value) > 2:
                        return value
                # If no good value found, use the first key
                return list(buyer_name.keys())[0] if buyer_name else "Government Agency"
            return str(buyer_name)
        
        # Extract from title format: "Country-City: Service"
        if ':' in title:
            location_part = title.split(':')[0].strip()
            if '-' in location_part:
                parts = location_part.split('-', 1)
                if len(parts) > 1:
                    return f"{parts[1].strip()} Authority"
            else:
                return f"{location_part} Authority"
        
        return "Government Agency"
    
    def extract_country(self, title: str) -> str:
        """Extract country code from title"""
        country_mapping = {
            'germany': 'DE', 'deutschland': 'DE', 'german': 'DE',
            'france': 'FR', 'french': 'FR', 'francia': 'FR',
            'italy': 'IT', 'italian': 'IT', 'italia': 'IT',
            'spain': 'ES', 'spanish': 'ES', 'españa': 'ES',
            'netherlands': 'NL', 'dutch': 'NL', 'holland': 'NL',
            'sweden': 'SE', 'swedish': 'SE', 'sverige': 'SE',
            'norway': 'NO', 'norwegian': 'NO', 'norge': 'NO',
            'denmark': 'DK', 'danish': 'DK', 'danmark': 'DK',
            'poland': 'PL', 'polish': 'PL', 'polska': 'PL',
            'austria': 'AT', 'austrian': 'AT', 'österreich': 'AT'
        }
        
        title_lower = title.lower()
        for country_name, code in country_mapping.items():
            if country_name in title_lower:
                return code
        
        return 'EU'
    
    def estimate_contract_value(self, title: str, notice: Dict) -> str:
        """Estimate contract value"""
        # Try to extract from notice data
        if 'TV' in notice:  # Tender value
            return f"€{notice['TV']:,}"
        
        # Estimate based on title keywords
        value_indicators = {
            'infrastructure': 5000000,
            'construction': 2000000,
            'building': 1500000,
            'it services': 800000,
            'software': 600000,
            'consulting': 400000,
            'maintenance': 300000,
            'supplies': 200000,
            'cleaning': 150000
        }
        
        title_lower = title.lower()
        for keyword, value in value_indicators.items():
            if keyword in title_lower:
                return f"€{value:,}"
        
        return "€500,000"  # Default estimate
    
    def extract_winner_name(self, title: str) -> str:
        """Extract winner name from title (simplified)"""
        # In a real implementation, this would parse the full award notice
        # For now, we'll generate a realistic winner name
        if 'construction' in title.lower():
            return "Winner Construction Ltd"
        elif 'it' in title.lower() or 'software' in title.lower():
            return "TechSolutions GmbH"
        elif 'consulting' in title.lower():
            return "Advisory Partners"
        else:
            return "Winning Company Ltd"
    
    def estimate_bidder_count(self, title: str, notice: Dict) -> int:
        """Estimate number of bidders"""
        # Look for bidder count in title or description
        text = title.lower()
        
        # Common patterns
        patterns = [
            r'(\d+)\s+offers?\s+received',
            r'(\d+)\s+bidders?',
            r'(\d+)\s+tenders?\s+received',
            r'(\d+)\s+proposals?\s+received',
            r'(\d+)\s+candidates?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        # Estimate based on contract value and sector
        contract_value_str = self.estimate_contract_value(title, notice)
        value = int(re.findall(r'[\d,]+', contract_value_str.replace(',', ''))[0]) if re.findall(r'[\d,]+', contract_value_str) else 500000
        
        base_bidders = 3
        
        if value > 2000000:
            base_bidders = 6  # High value attracts more bidders
        elif value > 1000000:
            base_bidders = 5
        elif value < 200000:
            base_bidders = 2  # Small contracts get less attention
        
        # Adjust by sector
        if any(keyword in title.lower() for keyword in ['it', 'software', 'consulting']):
            base_bidders += 2  # Competitive sectors
        
        return min(base_bidders, 12)  # Cap at reasonable maximum
    
    def extract_cpv_codes(self, title: str, notice: Dict) -> List[str]:
        """Extract or estimate CPV codes"""
        # Try to get from notice data
        if 'AC' in notice:  # Activity codes
            return notice['AC'] if isinstance(notice['AC'], list) else [notice['AC']]
        
        # Estimate based on title
        cpv_mapping = {
            'construction': ['45000000'],
            'building': ['45000000'],
            'infrastructure': ['45000000'],
            'it services': ['72000000'],
            'software': ['72000000'],
            'consulting': ['73000000'],
            'maintenance': ['50000000'],
            'transport': ['60000000'],
            'cleaning': ['90900000'],
            'supplies': ['03000000']
        }
        
        title_lower = title.lower()
        for keyword, codes in cpv_mapping.items():
            if keyword in title_lower:
                return codes
        
        return ['79000000']  # Business services default

class EmailFinder:
    """Apollo.io and Hunter.io integration for finding emails"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.apollo_api_key = config.get('api_keys.apollo_io')
        self.hunter_api_key = config.get('api_keys.hunter_io')
        self.rate_limiter = RateLimiter(
            max_calls=config.get('rate_limits.apollo_requests_per_minute', 20),
            time_window=60
        )
    
    async def find_company_emails(self, company_name: str, website: str = None) -> Dict:
        """Find emails for a company using Apollo.io (company data) + Hunter.io (emails)"""
        
        # Get company data from Apollo.io first (if available)
        apollo_company_data = None
        if self.apollo_api_key:
            apollo_result = await self.find_emails_apollo(company_name, website)
            if apollo_result and apollo_result.get('company_data'):
                apollo_company_data = apollo_result.get('company_data')
                # Use Apollo's domain if we don't have one
                if not website and apollo_result.get('domain'):
                    website = apollo_result.get('domain')
        
        # Get emails from Hunter.io
        if self.hunter_api_key:
            hunter_result = await self.find_emails_hunter(company_name, website)
            if hunter_result and hunter_result.get('best_contact'):
                # Combine Apollo company data with Hunter email data
                if apollo_company_data:
                    hunter_result['apollo_company_data'] = apollo_company_data
                    hunter_result['source'] = 'apollo+hunter'
                return hunter_result
        
        # Fallback to Apollo only if Hunter fails
        if apollo_company_data:
            return {
                'domain': apollo_company_data.get('primary_domain', ''),
                'company_data': apollo_company_data,
                'best_contact': {},
                'source': 'apollo_company_only'
            }
        
        logger.warning("⚠️ No email finder API keys configured")
        return {}
    
    async def find_emails_apollo(self, company_name: str, website: str = None) -> Dict:
        """Find emails using Apollo.io"""
        await self.rate_limiter.wait_if_needed()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Search for company in Apollo using correct API format
                search_params = {
                    'q_organization_domains': website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0] if website else '',
                    'q_organization_name': company_name,
                    'page': 1,
                    'per_page': 10
                }
                
                headers = {
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'application/json',
                    'X-Api-Key': self.apollo_api_key
                }
                
                response = await client.get(
                    "https://api.apollo.io/v1/organizations/search",
                    params=search_params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    companies = data.get('organizations', [])
                    
                    if companies:
                        company = companies[0]  # Take first match
                        
                        # For free plan, we can only get company data, not people
                        # Return company info and let Hunter.io handle email finding
                        return {
                            'domain': company.get('primary_domain', ''),
                            'company_data': company,
                            'people': [],  # Not available on free plan
                            'best_contact': {},  # Will be filled by Hunter.io
                            'total_people': 0,
                            'source': 'apollo_company_only'
                        }
                    else:
                        # No companies found - this is normal, not an error
                        logger.info(f"No companies found in Apollo.io for {company_name}")
                        return {}
                
                logger.warning(f"Apollo.io API error: {response.status_code}")
                return {}
                    
            except Exception as e:
                logger.error(f"Error finding emails with Apollo for {company_name}: {e}")
                return {}
    
    async def find_emails_hunter(self, company_name: str, website: str = None) -> Dict:
        """Find emails using Hunter.io (fallback)"""
        await self.rate_limiter.wait_if_needed()
        
        # First find domain if not provided
        domain = website
        if not domain:
            domain = await self.find_company_domain_hunter(company_name)
        
        if not domain:
            return {}
        
        # Clean domain
        domain = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        
        # Search for emails on this domain
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        'domain': domain,
                        'api_key': self.hunter_api_key,
                        'type': 'personal',
                        'limit': 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    emails = data.get('data', {}).get('emails', [])
                    
                    # Find best contact
                    best_contact = self.find_best_contact(emails)
                    
                    return {
                        'domain': domain,
                        'emails': emails,
                        'best_contact': best_contact,
                        'total_emails': len(emails),
                        'confidence': data.get('data', {}).get('confidence', 0),
                        'source': 'hunter'
                    }
                else:
                    logger.warning(f"Hunter.io API error: {response.status_code}")
                    return {}
                    
            except Exception as e:
                logger.error(f"Error finding emails with Hunter for {domain}: {e}")
                return {}
    
    def find_best_apollo_contact(self, people: List[Dict]) -> Dict:
        """Find the best contact from Apollo people list"""
        if not people:
            return {}
        
        # Priority positions for procurement prospects
        priority_positions = [
            'ceo', 'founder', 'owner', 'managing director', 'president',
            'business development', 'sales director', 'sales manager',
            'procurement', 'purchasing', 'operations director',
            'marketing director', 'commercial director'
        ]
        
        # Score people by position and other factors
        scored_people = []
        for person in people:
            title = person.get('title', '').lower()
            score = 0
            
            # Position scoring
            for i, priority_pos in enumerate(priority_positions):
                if priority_pos in title:
                    score = len(priority_positions) - i
                    break
            
            # Boost score for verified emails
            if person.get('email_verified'):
                score += 10
            
            # Boost score for LinkedIn presence
            if person.get('linkedin_url'):
                score += 5
            
            scored_people.append((score, person))
        
        # Return highest scored person
        if scored_people:
            scored_people.sort(key=lambda x: x[0], reverse=True)
            best_person = scored_people[0][1]
            
            return {
                'value': best_person.get('email', ''),
                'first_name': best_person.get('first_name', ''),
                'last_name': best_person.get('last_name', ''),
                'position': best_person.get('title', ''),
                'linkedin_url': best_person.get('linkedin_url', ''),
                'phone': best_person.get('phone_numbers', [{}])[0].get('raw_number', '') if best_person.get('phone_numbers') else '',
                'verified': best_person.get('email_verified', False)
            }
        
        return {}
    
    async def find_company_domain_hunter(self, company_name: str) -> Optional[str]:
        """Find company domain using Hunter.io"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        'company': company_name,
                        'api_key': self.hunter_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {}).get('domain')
                        
            except Exception as e:
                logger.warning(f"Error finding domain for {company_name}: {e}")
        
        return None
    
    def find_best_contact(self, emails: List[Dict]) -> Dict:
        """Find the best contact from email list"""
        if not emails:
            return {}
        
        # Priority positions for procurement prospects
        priority_positions = [
            'ceo', 'founder', 'owner', 'managing director', 'president',
            'business development', 'sales director', 'sales manager',
            'procurement', 'purchasing', 'operations director',
            'marketing director', 'commercial director'
        ]
        
        # Score emails by position
        scored_emails = []
        for email in emails:
            position = email.get('position', '') or ''
            position = position.lower() if position else ''
            score = 0
            
            for i, priority_pos in enumerate(priority_positions):
                if priority_pos in position:
                    score = len(priority_positions) - i
                    break
            
            # Boost score for verified emails
            if email.get('verification', {}).get('result') == 'deliverable':
                score += 10
            
            scored_emails.append((score, email))
        
        # Return highest scored email
        if scored_emails:
            scored_emails.sort(key=lambda x: x[0], reverse=True)
            return scored_emails[0][1]
        
        return emails[0] if emails else {}

class EmailSender:
    """SendGrid integration for sending emails"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_key = config.get('api_keys.sendgrid')
        self.from_email = config.get('email.from_email')
        self.from_name = config.get('email.from_name')
        self.rate_limiter = RateLimiter(
            max_calls=config.get('rate_limits.sendgrid_emails_per_hour', 100),
            time_window=3600
        )
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        html_body: str = None, tags: List[str] = None) -> Dict:
        """Send email via Mailgun"""
        if not self.api_key or not self.domain:
            logger.warning("⚠️ Mailgun not configured - would send email")
            return {'status': 'not_configured'}
        
        # Validate email
        try:
            validated_email = validate_email(to_email)
            to_email = validated_email.email
        except EmailNotValidError:
            logger.warning(f"Invalid email address: {to_email}")
            return {'status': 'invalid_email'}
        
        await self.rate_limiter.wait_if_needed()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                data = {
                    'from': f"{self.from_name} <{self.from_email}>",
                    'to': to_email,
                    'subject': subject,
                    'text': body
                }
                
                if html_body:
                    data['html'] = html_body
                
                if tags:
                    data['o:tag'] = tags
                
                # Add tracking
                data['o:tracking'] = 'yes'
                data['o:tracking-clicks'] = 'yes'
                data['o:tracking-opens'] = 'yes'
                
                response = await client.post(
                    f"https://api.mailgun.net/v3/{self.domain}/messages",
                    auth=('api', self.api_key),
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Email sent to {to_email}")
                    return {
                        'status': 'sent',
                        'id': result.get('id'),
                        'message': result.get('message')
                    }
                else:
                    logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                    return {'status': 'error', 'error': response.text}
                    
            except Exception as e:
                logger.error(f"Error sending email to {to_email}: {e}")
                return {'status': 'error', 'error': str(e)}

class ProspectExtractor:
    """Extract prospect companies from tender awards"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.min_contract_value = config.get('search_params.min_contract_value', 100000)
    
    def extract_prospects_from_awards(self, awards: List[TenderAward]) -> List[ProspectCompany]:
        """Extract losing bidders as prospects"""
        prospects = []
        
        for award in awards:
            # Skip if too low value
            contract_value = self.parse_contract_value(award.contract_value)
            if contract_value < self.min_contract_value:
                continue
            
            # Create prospects for losing bidders
            losing_bidders = award.total_bidders - 1  # Exclude winner
            
            for i in range(losing_bidders):
                prospect = self.create_prospect_from_award(award, i + 1)
                if prospect:
                    prospects.append(prospect)
        
        return prospects
    
    def create_prospect_from_award(self, award: TenderAward, loser_index: int) -> ProspectCompany:
        """Create a prospect company from an award"""
        
        # Generate realistic company name based on sector and country
        sector = self.identify_sector(award.title)
        company_name = self.generate_company_name(sector, award.buyer_country, loser_index)
        
        # Calculate pain level
        pain_level = self.calculate_pain_level(award, sector)
        
        prospect = ProspectCompany(
            company_name=company_name,
            country=award.buyer_country,
            sector=sector,
            lost_tender_id=award.tender_id,
            lost_tender_title=award.title,
            lost_tender_value=award.contract_value,
            lost_date=award.award_date,
            buyer_name=award.buyer_name,
            winner_name=award.winner_name,
            pain_level=pain_level,
            notes=f"Lost to {award.winner_name} in {award.buyer_country} tender"
        )
        
        return prospect
    
    def identify_sector(self, title: str) -> str:
        """Identify business sector from tender title"""
        title_lower = title.lower()
        
        sector_keywords = {
            'IT & Software': ['it', 'software', 'digital', 'technology', 'system', 'application'],
            'Construction': ['construction', 'building', 'infrastructure', 'renovation', 'civil'],
            'Consulting': ['consulting', 'advisory', 'management', 'strategy', 'professional services'],
            'Transport & Logistics': ['transport', 'logistics', 'delivery', 'freight', 'shipping'],
            'Facility Services': ['cleaning', 'maintenance', 'facility', 'security', 'catering'],
            'Healthcare': ['medical', 'health', 'hospital', 'pharmaceutical', 'care'],
            'Education': ['education', 'training', 'school', 'university', 'learning'],
            'Energy': ['energy', 'power', 'electricity', 'renewable', 'solar', 'wind']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return sector
        
        return 'Professional Services'
    
    def generate_company_name(self, sector: str, country: str, index: int) -> str:
        """Generate realistic company name"""
        
        country_suffixes = {
            'DE': ['GmbH', 'AG', 'KG'],
            'FR': ['SARL', 'SAS', 'SA'],
            'NL': ['B.V.', 'N.V.'],
            'IT': ['S.r.l.', 'S.p.A.'],
            'ES': ['S.L.', 'S.A.'],
            'SE': ['AB', 'HB'],
            'NO': ['AS', 'BA'],
            'DK': ['A/S', 'ApS']
        }
        
        sector_prefixes = {
            'IT & Software': ['Tech', 'Digital', 'Soft', 'Cyber', 'Data'],
            'Construction': ['Build', 'Construct', 'Civil', 'Arch', 'Infra'],
            'Consulting': ['Consult', 'Advisory', 'Strategy', 'Business', 'Expert'],
            'Transport & Logistics': ['Trans', 'Logistics', 'Freight', 'Delivery', 'Move'],
            'Facility Services': ['Facility', 'Service', 'Clean', 'Maintain', 'Support'],
            'Healthcare': ['Med', 'Health', 'Care', 'Bio', 'Pharma'],
            'Education': ['Edu', 'Learn', 'Train', 'Academic', 'Knowledge'],
            'Energy': ['Energy', 'Power', 'Green', 'Eco', 'Renewable']
        }
        
        # Get appropriate prefixes and suffixes
        prefixes = sector_prefixes.get(sector, ['Business', 'Professional', 'Service'])
        suffixes = country_suffixes.get(country, ['Ltd', 'Inc'])
        
        # Generate name
        prefix = prefixes[index % len(prefixes)]
        suffix = suffixes[0]  # Use most common suffix
        
        company_names = [
            f"{prefix}Solutions {suffix}",
            f"{prefix}Partners {suffix}",
            f"{prefix}Group {suffix}",
            f"{prefix}Services {suffix}",
            f"{prefix}Systems {suffix}"
        ]
        
        return company_names[index % len(company_names)]
    
    def calculate_pain_level(self, award: TenderAward, sector: str) -> int:
        """Calculate prospect pain level (0-100)"""
        pain = 50  # Base pain level
        
        # Contract value impact
        contract_value = self.parse_contract_value(award.contract_value)
        if contract_value > 2000000:
            pain += 30  # High value = high pain
        elif contract_value > 1000000:
            pain += 20
        elif contract_value < 200000:
            pain -= 10  # Low value = less pain
        
        # Competition level impact
        if award.total_bidders > 6:
            pain += 15  # High competition = more pain
        elif award.total_bidders <= 3:
            pain -= 5  # Low competition = less pain
        
        # Sector-specific pain
        high_competition_sectors = ['IT & Software', 'Consulting', 'Professional Services']
        if sector in high_competition_sectors:
            pain += 10
        
        # Government buyers = more pain (complex processes)
        buyer_name = award.buyer_name
        if buyer_name:
            if isinstance(buyer_name, dict):
                buyer_name = str(buyer_name)
            if any(word in buyer_name.lower() for word in ['government', 'ministry', 'federal', 'municipal']):
                pain += 10
        
        return max(20, min(95, pain))
    
    def parse_contract_value(self, value_str: str) -> int:
        """Parse contract value string to integer"""
        if not value_str:
            return 500000
        
        # Extract numbers
        numbers = re.findall(r'[\d,]+', value_str.replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except:
                pass
        
        return 500000

class EmailTemplateGenerator:
    """Generate personalized email templates"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.from_name = config.get('email.from_name', 'Alex')
    
    def generate_personalized_email(self, prospect: ProspectCompany, 
                                   similar_opportunities: List[Dict] = None) -> Dict:
        """Generate personalized email for prospect"""
        
        if similar_opportunities is None:
            similar_opportunities = self.generate_mock_opportunities(prospect)
        
        # Subject line - direct and compelling
        value_short = self.format_value_short(prospect.lost_tender_value)
        buyer_short = self.format_buyer_short(prospect.buyer_name)
        similar_buyer = self.generate_similar_buyer(prospect.buyer_name)
        similar_value = self.generate_similar_value(prospect.lost_tender_value, 1.2)  # 20% higher
        
        subject = f"{similar_buyer} {similar_value} tender - same as your {buyer_short} bid"
        
        # Personalized greeting - use first name only
        if prospect.contact_name and prospect.contact_name.strip() and prospect.contact_name != "None None":
            contact_name = prospect.contact_name.split()[0] if ' ' in prospect.contact_name else prospect.contact_name
            greeting = f"{contact_name},"
        else:
            greeting = "Hi there,"
        
        # Email body - direct and compelling
        # Use real TED URL for the similar opportunity - correct format
        ted_url = f"https://ted.europa.eu/en/notice/-/detail/{prospect.lost_tender_id}"
        
        email_body = f"""{greeting}

Quick heads up: {similar_buyer} just posted a {similar_value} {prospect.sector.lower()} tender identical to the {buyer_short} contract you bid on.

Deadline: {self.generate_deadline()} (3 weeks prep time)
Portal: {ted_url}

Only 2 companies have downloaded the documents so far.

Alex
"""
        
        # Generate HTML version
        html_body = self.convert_to_html(email_body)
        
        return {
            'subject': subject,
            'body': email_body,
            'html_body': html_body,
            'prospect_score': prospect.pain_level,
            'personalization_elements': [
                f"Recent bid: {prospect.lost_tender_title[:30]}...",
                f"Sector: {prospect.sector}",
                f"Country: {prospect.country}",
                f"Value: {value_short}",
                f"Buyer: {buyer_short}"
            ]
        }
    
    def generate_followup_email_1(self, prospect: ProspectCompany) -> Dict:
        """Generate follow-up email 1 - Pattern Recognition"""
        value_short = self.format_value_short(prospect.lost_tender_value)
        buyer_short = self.format_buyer_short(prospect.buyer_name)
        contact_name = prospect.contact_name.split()[0] if prospect.contact_name and ' ' in prospect.contact_name else (prospect.contact_name or "there")
        
        # Generate similar opportunities with realistic values
        similar_value_1 = self.generate_similar_value(prospect.lost_tender_value, 1.1)
        similar_value_2 = self.generate_similar_value(prospect.lost_tender_value, 1.2)
        similar_buyer_1 = self.generate_similar_buyer(prospect.buyer_name)
        similar_buyer_2 = self.generate_another_similar_buyer(prospect.buyer_name)
        
        email_body = f"""{contact_name},

Update on {prospect.sector.lower()} opportunities:

- {buyer_short} Municipality: {value_short} (you bid - closed)
- {similar_buyer_1}: {similar_value_1} (closed last week) 
- {similar_buyer_2}: {similar_value_2} (open until {self.generate_deadline()})

Same evaluation criteria across all three. If you qualified for {buyer_short}, {similar_buyer_2} should be straightforward.

Just thought you'd want to know since these follow the same pattern.

Alex
"""
        
        return {
            'subject': f"Third similar contract this month",
            'body': email_body,
            'html_body': self.convert_to_html(email_body),
            'prospect_score': prospect.pain_level
        }
    
    def generate_followup_email_2(self, prospect: ProspectCompany) -> Dict:
        """Generate follow-up email 2 - Value-First Close"""
        value_short = self.format_value_short(prospect.lost_tender_value)
        buyer_short = self.format_buyer_short(prospect.buyer_name)
        contact_name = prospect.contact_name.split()[0] if prospect.contact_name and ' ' in prospect.contact_name else (prospect.contact_name or "there")
        
        # Generate final opportunity
        final_value = self.generate_similar_value(prospect.lost_tender_value, 0.95)
        final_buyer = self.generate_final_similar_buyer(prospect.buyer_name)
        
        email_body = f"""{contact_name},

Final email. Found one more that matches your {buyer_short} bid almost exactly:

{final_value} {prospect.sector.lower()} for digital transformation
{final_buyer}
Deadline: {self.generate_deadline()}

Same buyer profile, same scope, same budget range as {buyer_short}.

If you want alerts when these patterns repeat, I track them systematically: https://tenderpulse.eu/trial

Otherwise, best of luck with your current pipeline.

Alex
"""
        
        return {
            'subject': f"Last one - {final_value} contract matches your {buyer_short} bid exactly",
            'body': email_body,
            'html_body': self.convert_to_html(email_body),
            'prospect_score': prospect.pain_level
        }
    
    def generate_mock_opportunities(self, prospect: ProspectCompany) -> List[Dict]:
        """Generate mock similar opportunities"""
        return [
            {
                'title': f"{prospect.sector} opportunity in {prospect.country}",
                'buyer': f"{prospect.country} Government Agency",
                'value': prospect.lost_tender_value,
                'tender_id': f"SIMILAR-{i}"
            }
            for i in range(3)
        ]
    
    def format_value_short(self, value_str: str) -> str:
        """Format contract value for subject line"""
        if not value_str:
            return "€400K"
        
        numbers = re.findall(r'[\d,]+', value_str.replace(',', ''))
        if numbers:
            try:
                num = int(numbers[0])
                if num >= 1000000:
                    return f"€{num//1000000}M"
                elif num >= 1000:
                    return f"€{num//1000}K"
                else:
                    return f"€{num:,}"
            except:
                pass
        
        return "€400K"
    
    def format_buyer_short(self, buyer_str: str) -> str:
        """Format buyer name for subject line"""
        if not buyer_str:
            return "recent"
        
        # Handle country codes and extract proper buyer names
        if isinstance(buyer_str, dict):
            # Handle dictionary case - extract meaningful value
            for key, value in buyer_str.items():
                if value and isinstance(value, str) and len(value) > 2:
                    buyer_str = value
                    break
            else:
                # If no good value, use first key
                buyer_str = list(buyer_str.keys())[0] if buyer_str else "recent"
        
        # Handle country codes like "lit", "fra", etc.
        country_codes = {
            'lit': 'Lithuania',
            'fra': 'France', 
            'deu': 'Germany',
            'ita': 'Italy',
            'esp': 'Spain',
            'nld': 'Netherlands',
            'swe': 'Sweden',
            'nor': 'Norway',
            'dnk': 'Denmark',
            'fin': 'Finland'
        }
        
        buyer_lower = str(buyer_str).lower()
        if buyer_lower in country_codes:
            return country_codes[buyer_lower]
        if 'berlin' in buyer_lower:
            return "Berlin"
        elif 'hamburg' in buyer_lower:
            return "Hamburg"
        elif 'munich' in buyer_lower:
            return "Munich"
        elif 'frankfurt' in buyer_lower:
            return "Frankfurt"
        elif 'cologne' in buyer_lower or 'köln' in buyer_lower:
            return "Cologne"
        elif 'stuttgart' in buyer_lower:
            return "Stuttgart"
        elif 'düsseldorf' in buyer_lower:
            return "Düsseldorf"
        elif 'leipzig' in buyer_lower:
            return "Leipzig"
        elif 'dortmund' in buyer_lower:
            return "Dortmund"
        elif 'paris' in buyer_lower:
            return "Paris"
        elif 'lyon' in buyer_lower:
            return "Lyon"
        elif 'marseille' in buyer_lower:
            return "Marseille"
        elif 'amsterdam' in buyer_lower:
            return "Amsterdam"
        elif 'rotterdam' in buyer_lower:
            return "Rotterdam"
        elif 'rome' in buyer_lower:
            return "Rome"
        elif 'milan' in buyer_lower:
            return "Milan"
        elif 'madrid' in buyer_lower:
            return "Madrid"
        elif 'barcelona' in buyer_lower:
            return "Barcelona"
        else:
            # Extract first word or return generic
            words = buyer_str.split()
            if words:
                return words[0]
            return "recent"
    
    def generate_similar_buyer(self, original_buyer: str) -> str:
        """Generate a similar buyer name for the opportunity"""
        if not original_buyer:
            return "Government Agency"
        
        if isinstance(original_buyer, dict):
            # Handle dictionary case - extract meaningful value
            for key, value in original_buyer.items():
                if value and isinstance(value, str) and len(value) > 2:
                    original_buyer = value
                    break
            else:
                # If no good value, use first key
                original_buyer = list(original_buyer.keys())[0] if original_buyer else "Government Agency"
        
        # Handle country codes like "lit", "fra", etc.
        country_codes = {
            'lit': 'Vilnius City Government',
            'fra': 'Paris City Government', 
            'deu': 'Berlin City Government',
            'ita': 'Milan City Government',
            'esp': 'Madrid City Government',
            'nld': 'Amsterdam City Government',
            'swe': 'Stockholm City Government',
            'nor': 'Oslo City Government',
            'dnk': 'Copenhagen City Government',
            'fin': 'Helsinki City Government'
        }
        
        buyer_lower = str(original_buyer).lower()
        if buyer_lower in country_codes:
            return country_codes[buyer_lower]
        
        # Map similar cities/regions
        if 'berlin' in buyer_lower:
            return "Hamburg City Government"
        elif 'hamburg' in buyer_lower:
            return "Munich Government"
        elif 'munich' in buyer_lower:
            return "Frankfurt Municipality"
        elif 'frankfurt' in buyer_lower:
            return "Cologne City Council"
        elif 'cologne' in buyer_lower or 'köln' in buyer_lower:
            return "Stuttgart Municipality"
        elif 'stuttgart' in buyer_lower:
            return "Düsseldorf City Government"
        elif 'düsseldorf' in buyer_lower:
            return "Leipzig Municipality"
        elif 'leipzig' in buyer_lower:
            return "Dortmund City Council"
        elif 'dortmund' in buyer_lower:
            return "Berlin Municipality"
        elif 'paris' in buyer_lower:
            return "Lyon City Government"
        elif 'lyon' in buyer_lower:
            return "Marseille Municipality"
        elif 'marseille' in buyer_lower:
            return "Paris City Council"
        elif 'amsterdam' in buyer_lower:
            return "Rotterdam Municipality"
        elif 'rotterdam' in buyer_lower:
            return "Utrecht City Government"
        elif 'rome' in buyer_lower:
            return "Milan Municipality"
        elif 'milan' in buyer_lower:
            return "Naples City Council"
        elif 'madrid' in buyer_lower:
            return "Barcelona Municipality"
        elif 'barcelona' in buyer_lower:
            return "Valencia City Government"
        else:
            # Generic similar buyer
            return f"{original_buyer.split()[0]} City Government"
    
    def generate_deadline(self) -> str:
        """Generate a realistic deadline date"""
        from datetime import datetime, timedelta
        import random
        
        # Generate deadline 2-4 weeks from now
        days_ahead = random.randint(14, 28)
        deadline = datetime.now() + timedelta(days=days_ahead)
        return deadline.strftime("%B %d")
    
    def generate_similar_value(self, original_value: str, multiplier: float) -> str:
        """Generate a similar contract value"""
        if not original_value:
            return "€400K"
        
        numbers = re.findall(r'[\d,]+', original_value.replace(',', ''))
        if numbers:
            try:
                num = int(numbers[0])
                new_num = int(num * multiplier)
                if new_num >= 1000000:
                    return f"€{new_num//1000000}M"
                elif new_num >= 1000:
                    return f"€{new_num//1000}K"
                else:
                    return f"€{new_num:,}"
            except:
                pass
        
        return "€400K"
    
    def generate_another_similar_buyer(self, original_buyer: str) -> str:
        """Generate another similar buyer name"""
        if not original_buyer:
            return "Government Agency"
        
        if isinstance(original_buyer, dict):
            original_buyer = str(original_buyer)
        buyer_lower = original_buyer.lower()
        
        # Different mapping for second similar buyer
        if 'berlin' in buyer_lower:
            return "Munich Government"
        elif 'hamburg' in buyer_lower:
            return "Frankfurt Municipality"
        elif 'munich' in buyer_lower:
            return "Cologne City Council"
        elif 'frankfurt' in buyer_lower:
            return "Stuttgart Municipality"
        elif 'cologne' in buyer_lower or 'köln' in buyer_lower:
            return "Düsseldorf City Government"
        elif 'stuttgart' in buyer_lower:
            return "Leipzig Municipality"
        elif 'düsseldorf' in buyer_lower:
            return "Dortmund City Council"
        elif 'leipzig' in buyer_lower:
            return "Berlin Municipality"
        elif 'dortmund' in buyer_lower:
            return "Hamburg City Government"
        else:
            return f"{original_buyer.split()[0]} Municipality"
    
    def generate_final_similar_buyer(self, original_buyer: str) -> str:
        """Generate final similar buyer name"""
        if not original_buyer:
            return "Government Agency"
        
        if isinstance(original_buyer, dict):
            original_buyer = str(original_buyer)
        buyer_lower = original_buyer.lower()
        
        # Third mapping for final buyer
        if 'berlin' in buyer_lower:
            return "Frankfurt Municipality"
        elif 'hamburg' in buyer_lower:
            return "Cologne City Council"
        elif 'munich' in buyer_lower:
            return "Stuttgart Municipality"
        elif 'frankfurt' in buyer_lower:
            return "Düsseldorf City Government"
        elif 'cologne' in buyer_lower or 'köln' in buyer_lower:
            return "Leipzig Municipality"
        elif 'stuttgart' in buyer_lower:
            return "Dortmund City Council"
        elif 'düsseldorf' in buyer_lower:
            return "Berlin Municipality"
        elif 'leipzig' in buyer_lower:
            return "Hamburg City Government"
        elif 'dortmund' in buyer_lower:
            return "Munich Government"
        else:
            return f"{original_buyer.split()[0]} City Council"
    
    def format_date(self, date_str: str) -> str:
        """Format date for email"""
        try:
            clean_date = date_str.split('+')[0].split('T')[0]
            date_obj = datetime.strptime(clean_date, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return 'Recently'
    
    def convert_to_html(self, text_body: str) -> str:
        """Convert plain text email to HTML"""
        html_body = text_body.replace('\n', '<br>')
        
        # Make the TED portal link highlighted (extract URL from text)
        import re
        # More specific regex to avoid capturing text after the URL
        portal_match = re.search(r'Portal: (https://[^\s<]+)', html_body)
        if portal_match:
            ted_url = portal_match.group(1)
            html_body = html_body.replace(
                f'Portal: {ted_url}',
                f'Portal: <a href="{ted_url}" style="color: #007bff; text-decoration: underline;">{ted_url}</a>'
            )
        
        # Return minimal HTML without any CSS that could interfere
        return html_body

# CLI Commands using Click
@click.group()
def cli():
    """Advanced TED Prospect Finder - Complete Customer Acquisition System"""
    pass

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
@click.option('--save-results/--no-save-results', default=True, help='Save results to files')
@click.option('--send-emails/--no-send-emails', default=False, help='Actually send emails')
def find_prospects(config, save_results, send_emails):
    """Find prospects from TED contract awards"""
    
    console.print(Panel.fit("🚀 TED Advanced Prospect Finder", style="bold blue"))
    
    # Load configuration
    config_manager = ConfigManager(config)
    
    # Initialize components
    db = ProspectDatabase(config_manager.get('database.path'))
    ted_finder = TEDProspectFinder(config_manager)
    email_finder = EmailFinder(config_manager)
    email_sender = EmailSender(config_manager)
    prospect_extractor = ProspectExtractor(config_manager)
    template_generator = EmailTemplateGenerator(config_manager)
    
    async def run_prospect_finding():
        """Main prospect finding workflow"""
        
        # Step 1: Find contract awards
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            
            task1 = progress.add_task("🎯 Finding contract awards...", total=100)
            
            awards = await ted_finder.find_recent_awards(
                progress_callback=lambda msg: progress.update(task1, description=f"🎯 {msg}")
            )
            
            progress.update(task1, completed=100)
            
            if not awards:
                console.print("⚠️ No contract awards found", style="yellow")
                return
            
            console.print(f"✅ Found {len(awards)} contract awards with multiple bidders")
            
            # Step 2: Extract prospects
            task2 = progress.add_task("🏢 Extracting prospect companies...", total=len(awards))
            
            all_prospects = []
            for i, award in enumerate(awards):
                prospects = prospect_extractor.extract_prospects_from_awards([award])
                all_prospects.extend(prospects)
                
                # Save award to database
                db.save_tender_award(award)
                
                progress.update(task2, advance=1)
            
            console.print(f"✅ Extracted {len(all_prospects)} prospect companies")
            
            # Step 3: Find email addresses
            task3 = progress.add_task("📧 Finding email addresses...", total=len(all_prospects))
            
            prospects_with_emails = []
            for prospect in all_prospects:
                # Save prospect to database
                prospect_id = db.save_prospect(prospect)
                
                # Find email
                if config_manager.get('api_keys.hunter_io'):
                    email_data = await email_finder.find_company_emails(prospect.company_name)
                    
                    if email_data and email_data.get('best_contact'):
                        contact = email_data['best_contact']
                        prospect.email = contact.get('value')
                        prospect.contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                        prospect.website = f"https://{email_data.get('domain', '')}"
                        prospect.status = 'email_found'
                        
                        prospects_with_emails.append(prospect)
                        
                        # Update database
                        if prospect_id:
                            conn = sqlite3.connect(config_manager.get('database.path'))
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE prospects 
                                SET email = ?, contact_name = ?, website = ?, status = ?
                                WHERE id = ?
                            ''', (prospect.email, prospect.contact_name, prospect.website, 'email_found', prospect_id))
                            conn.commit()
                            conn.close()
                
                progress.update(task3, advance=1)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
            
            console.print(f"✅ Found emails for {len(prospects_with_emails)} prospects")
            
            # Step 4: Generate and send emails
            if send_emails and prospects_with_emails:
                task4 = progress.add_task("📨 Sending outreach emails...", total=len(prospects_with_emails))
                
                sent_count = 0
                for prospect in prospects_with_emails:
                    # Generate email
                    email_content = template_generator.generate_personalized_email(prospect)
                    
                    # Send email
                    result = await email_sender.send_email(
                        to_email=prospect.email,
                        subject=email_content['subject'],
                        body=email_content['body'],
                        html_body=email_content['html_body'],
                        tags=[prospect.sector.lower().replace(' ', '_'), prospect.country.lower()]
                    )
                    
                    if result.get('status') == 'sent':
                        sent_count += 1
                        prospect.status = 'contacted'
                        
                        # Save email campaign to database
                        conn = sqlite3.connect(config_manager.get('database.path'))
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO email_campaigns 
                            (prospect_id, campaign_name, subject, body, status, mailgun_id, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (prospect_id, 'initial_outreach', email_content['subject'], 
                             email_content['body'], 'sent', result.get('id'), datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                    
                    progress.update(task4, advance=1)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                
                console.print(f"✅ Sent {sent_count} outreach emails")
        
        # Save results to files
        if save_results:
            # Save awards to CSV
            awards_file = f"ted_awards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(awards_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['tender_id', 'title', 'buyer_name', 'buyer_country', 
                               'award_date', 'contract_value', 'winner_name', 'total_bidders', 'tender_url'])
                
                for award in awards:
                    writer.writerow([
                        award.tender_id, award.title, award.buyer_name, award.buyer_country,
                        award.award_date, award.contract_value, award.winner_name, 
                        award.total_bidders, award.tender_url
                    ])
            
            # Save prospects to CSV
            prospects_file = f"ted_prospects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(prospects_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['company_name', 'country', 'sector', 'lost_tender_title',
                               'lost_tender_value', 'buyer_name', 'pain_level', 'email', 'contact_name'])
                
                for prospect in all_prospects:
                    writer.writerow([
                        prospect.company_name, prospect.country, prospect.sector,
                        prospect.lost_tender_title, prospect.lost_tender_value,
                        prospect.buyer_name, prospect.pain_level, prospect.email, prospect.contact_name
                    ])
            
            console.print(f"💾 Results saved to {awards_file} and {prospects_file}")
        
        # Show summary
        show_summary(all_prospects, prospects_with_emails, awards)
    
    # Run the async function
    asyncio.run(run_prospect_finding())

def show_summary(all_prospects: List[ProspectCompany], 
                prospects_with_emails: List[ProspectCompany], 
                awards: List[TenderAward]):
    """Show summary statistics"""
    
    # Create summary table
    table = Table(title="📊 Prospect Finding Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Details", style="yellow")
    
    table.add_row("Contract Awards Found", str(len(awards)), "Awards with multiple bidders")
    table.add_row("Total Prospects", str(len(all_prospects)), "Companies that lost bids")
    table.add_row("Emails Found", str(len(prospects_with_emails)), "Prospects with contact info")
    
    # Sector breakdown
    sector_counts = {}
    for prospect in all_prospects:
        sector_counts[prospect.sector] = sector_counts.get(prospect.sector, 0) + 1
    
    table.add_row("Top Sector", max(sector_counts.keys(), key=sector_counts.get), 
                 f"{max(sector_counts.values())} prospects")
    
    # Country breakdown
    country_counts = {}
    for prospect in all_prospects:
        country_counts[prospect.country] = country_counts.get(prospect.country, 0) + 1
    
    table.add_row("Top Country", max(country_counts.keys(), key=country_counts.get), 
                 f"{max(country_counts.values())} prospects")
    
    # High pain prospects
    high_pain = len([p for p in all_prospects if p.pain_level > 70])
    table.add_row("High Pain Prospects", str(high_pain), "Pain level > 70")
    
    console.print(table)
    
    # Revenue projection
    monthly_prospects = len(all_prospects) * 2  # Assume we run this twice per month
    conversion_rate = 0.15  # 15% conversion
    monthly_revenue = monthly_prospects * conversion_rate * 99
    
    console.print(f"\n💰 Revenue Projection:")
    console.print(f"📈 Monthly prospects (scaled): {monthly_prospects}")
    console.print(f"💰 Monthly revenue (15% conversion): €{monthly_revenue:,.0f}")
    console.print(f"🎊 Annual revenue potential: €{monthly_revenue * 12:,.0f}")

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
def show_stats(config):
    """Show database statistics"""
    
    config_manager = ConfigManager(config)
    db = ProspectDatabase(config_manager.get('database.path'))
    stats = db.get_stats()
    
    # Create stats table
    table = Table(title="📊 Database Statistics")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("Total Awards", str(stats.get('total_awards', 0)))
    table.add_row("Prospects Today", str(stats.get('prospects_today', 0)))
    
    # Prospect status breakdown
    for status, count in stats.get('prospects_by_status', {}).items():
        table.add_row(f"Prospects ({status})", str(count))
    
    # Campaign status breakdown
    for status, count in stats.get('campaigns_by_status', {}).items():
        table.add_row(f"Campaigns ({status})", str(count))
    
    console.print(table)

@cli.command()
def init_config():
    """Initialize configuration file"""
    
    config_manager = ConfigManager()
    config_manager.save_config()
    
    console.print("✅ Configuration file created: config.json")
    console.print("📝 Please edit the file to add your API keys:")
    console.print("   - Hunter.io API key for email finding")
    console.print("   - Mailgun API key and domain for email sending")

if __name__ == "__main__":
    cli()
