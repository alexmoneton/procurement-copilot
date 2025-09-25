#!/usr/bin/env python3
"""
TenderPulse Automation System - Complete Customer Acquisition Automation
Daily scheduling, duplicate detection, follow-up sequences, and CRM integration

Features:
- Daily scheduled prospect finding
- Duplicate detection and prevention
- Automated follow-up email sequences
- CRM integration preparation
- Backup and logging system
- Performance monitoring
- Error handling and recovery
"""

import os
import json
import sqlite3
import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import our existing components
from advanced_ted_prospect_finder import (
    ConfigManager, ProspectDatabase, TEDProspectFinder, 
    EmailFinder, EmailSender, ProspectExtractor, EmailTemplateGenerator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('automation')

@dataclass
class AutomationConfig:
    """Configuration for automation system"""
    daily_run_time: str = "09:00"  # 9 AM daily
    max_prospects_per_day: int = 100
    follow_up_delays: List[int] = None  # Days between follow-ups
    duplicate_check_fields: List[str] = None
    backup_frequency: str = "daily"  # daily, weekly, monthly
    crm_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    def __post_init__(self):
        if self.follow_up_delays is None:
            self.follow_up_delays = [3, 7, 14, 30]  # Follow up after 3, 7, 14, 30 days
        if self.duplicate_check_fields is None:
            self.duplicate_check_fields = ['company_name', 'email', 'lost_tender_id']

class DuplicateDetector:
    """Advanced duplicate detection system"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_duplicate_tables()
    
    def init_duplicate_tables(self):
        """Initialize duplicate detection tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Duplicate hashes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicate_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_value TEXT UNIQUE NOT NULL,
                prospect_id INTEGER,
                created_at TEXT,
                FOREIGN KEY (prospect_id) REFERENCES prospects (id)
            )
        ''')
        
        # Duplicate groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicate_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_hash TEXT NOT NULL,
                prospect_ids TEXT,  -- JSON array of prospect IDs
                created_at TEXT,
                resolved_at TEXT,
                resolution_type TEXT  -- merged, kept, deleted
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_prospect_hash(self, prospect_data: Dict) -> str:
        """Generate hash for duplicate detection"""
        # Create hash from key fields
        hash_fields = [
            prospect_data.get('company_name', '').lower().strip(),
            prospect_data.get('email', '').lower().strip(),
            prospect_data.get('lost_tender_id', ''),
            prospect_data.get('country', ''),
            prospect_data.get('sector', '')
        ]
        
        # Combine and hash
        combined = '|'.join(hash_fields)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def check_duplicate(self, prospect_data: Dict) -> Optional[int]:
        """Check if prospect is duplicate, return existing prospect ID if found"""
        prospect_hash = self.generate_prospect_hash(prospect_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT prospect_id FROM duplicate_hashes WHERE hash_value = ?', (prospect_hash,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else None
    
    def mark_as_duplicate(self, prospect_id: int, prospect_data: Dict):
        """Mark prospect as processed for duplicate detection"""
        prospect_hash = self.generate_prospect_hash(prospect_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO duplicate_hashes (hash_value, prospect_id, created_at)
                VALUES (?, ?, ?)
            ''', (prospect_hash, prospect_id, datetime.now().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            # Hash already exists, that's fine
            pass
        finally:
            conn.close()
    
    def find_similar_prospects(self, prospect_data: Dict, similarity_threshold: float = 0.8) -> List[Dict]:
        """Find similar prospects using fuzzy matching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all prospects for comparison
        cursor.execute('SELECT * FROM prospects')
        columns = [description[0] for description in cursor.description]
        all_prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        similar_prospects = []
        company_name = prospect_data.get('company_name', '').lower()
        
        for prospect in all_prospects:
            existing_name = prospect.get('company_name', '').lower()
            
            # Simple similarity check (can be enhanced with fuzzy matching)
            if self.calculate_similarity(company_name, existing_name) >= similarity_threshold:
                similar_prospects.append(prospect)
        
        return similar_prospects
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple implementation)"""
        if not str1 or not str2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

class FollowUpSequencer:
    """Automated follow-up email sequences"""
    
    def __init__(self, config: ConfigManager, db: ProspectDatabase):
        self.config = config
        self.db = db
        self.email_sender = EmailSender(config)
        self.template_generator = EmailTemplateGenerator(config)
    
    def get_prospects_for_follow_up(self) -> List[Dict]:
        """Get prospects that need follow-up emails"""
        conn = sqlite3.connect(self.config.get('database.path'))
        cursor = conn.cursor()
        
        # Get prospects that were contacted but haven't responded
        cursor.execute('''
            SELECT p.*, c.sent_at as last_email_sent
            FROM prospects p
            LEFT JOIN email_campaigns c ON p.id = c.prospect_id
            WHERE p.status IN ('contacted', 'email_found')
            AND p.email IS NOT NULL
            AND (c.sent_at IS NULL OR c.sent_at < date('now', '-3 days'))
            AND p.id NOT IN (
                SELECT DISTINCT prospect_id 
                FROM email_campaigns 
                WHERE replied_at IS NOT NULL
            )
            ORDER BY c.sent_at ASC
        ''')
        
        columns = [description[0] for description in cursor.description]
        prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return prospects
    
    def generate_follow_up_email(self, prospect: Dict, sequence_number: int) -> Dict:
        """Generate follow-up email based on sequence number"""
        
        # Create prospect object for template generation
        from advanced_ted_prospect_finder import ProspectCompany
        prospect_obj = ProspectCompany(
            company_name=prospect['company_name'],
            country=prospect['country'],
            sector=prospect['sector'],
            lost_tender_id=prospect['lost_tender_id'],
            lost_tender_title=prospect['lost_tender_title'],
            lost_tender_value=prospect['lost_tender_value'],
            lost_date=prospect['lost_date'],
            buyer_name=prospect['buyer_name'],
            winner_name=prospect['winner_name'],
            pain_level=prospect['pain_level'],
            email=prospect.get('email'),
            contact_name=prospect.get('contact_name')
        )
        
        # Different templates for different sequence numbers
        if sequence_number == 1:  # 3 days later
            subject = f"Did you see these {prospect['sector']} opportunities in {prospect['country']}?"
            body = self.generate_gentle_reminder(prospect_obj)
        elif sequence_number == 2:  # 7 days later
            subject = f"Last chance - 2 new {prospect['sector']} tenders closing soon"
            body = self.generate_urgency_email(prospect_obj)
        elif sequence_number == 3:  # 14 days later
            subject = f"How's your procurement pipeline looking?"
            body = self.generate_check_in_email(prospect_obj)
        else:  # 30+ days later
            subject = f"New {prospect['sector']} opportunities in {prospect['country']}"
            body = self.generate_fresh_opportunities_email(prospect_obj)
        
        return {
            'subject': subject,
            'body': body,
            'html_body': self.template_generator.convert_to_html(body)
        }
    
    def generate_gentle_reminder(self, prospect: ProspectCompany) -> str:
        """Generate gentle reminder email"""
        return f"""Hi {prospect.contact_name or 'there'},

I wanted to follow up on my email about the {prospect.sector} opportunities in {prospect.country}.

I know you're busy, but I found 3 new tenders that might be perfect for your business:

1. Similar {prospect.sector} project in {prospect.country}
   💰 Est. Value: {prospect.lost_tender_value}
   ⏰ Deadline: Next week
   
2. {prospect.buyer_name} has another tender coming up
   💰 Est. Value: €800,000
   ⏰ Deadline: 2 weeks
   
3. New infrastructure project in {prospect.country}
   💰 Est. Value: €1.2M
   ⏰ Deadline: 3 weeks

These opportunities won't last long. Want me to set up your free TenderPulse trial so you never miss another one?

Just reply "YES" and I'll get you access today.

Best regards,
Alex
TenderPulse

P.S. - The next big {prospect.sector} contract in {prospect.country} could be published tomorrow."""

    def generate_urgency_email(self, prospect: ProspectCompany) -> str:
        """Generate urgency-based email"""
        return f"""Hi {prospect.contact_name or 'there'},

I don't want you to miss out on these {prospect.sector} opportunities closing soon:

🚨 URGENT - 2 tenders closing this week:
1. {prospect.country} Government {prospect.sector} project
   💰 Value: {prospect.lost_tender_value}
   ⏰ Deadline: 3 days
   
2. Similar project to the one you bid on
   💰 Value: €900,000
   ⏰ Deadline: 5 days

Most companies miss 80% of relevant opportunities because they're scattered across 27+ different procurement portals.

TenderPulse monitors ALL of them 24/7 and sends you early alerts.

Want to see what you're missing? I can set up a free trial right now.

Just reply "YES" and I'll get you access in the next 5 minutes.

Best regards,
Alex
TenderPulse

P.S. - These tenders close this week. Don't let another opportunity slip by."""

    def generate_check_in_email(self, prospect: ProspectCompany) -> str:
        """Generate check-in email"""
        return f"""Hi {prospect.contact_name or 'there'},

How's your procurement pipeline looking these days?

I know you recently bid on that {prospect.lost_tender_value} {prospect.sector} project with {prospect.buyer_name}. 

While that one didn't work out, I wanted to check in and see if you're finding other opportunities in {prospect.country}.

If you're still manually searching through procurement portals, you're probably missing 80% of relevant tenders.

TenderPulse users win 34% more contracts because they:
✓ Get early alerts (more time to prepare quality bids)
✓ Focus on opportunities they can actually win
✓ Never miss deadlines with automated reminders

Interested in a quick demo? I can show you exactly which opportunities you're missing right now.

Just reply "DEMO" and I'll set up a 15-minute call.

Best regards,
Alex
TenderPulse

P.S. - No pressure, just want to make sure you're not missing out on opportunities."""

    def generate_fresh_opportunities_email(self, prospect: ProspectCompany) -> str:
        """Generate fresh opportunities email"""
        return f"""Hi {prospect.contact_name or 'there'},

I found some fresh {prospect.sector} opportunities in {prospect.country} that might interest you:

🆕 NEW OPPORTUNITIES:
1. {prospect.country} Infrastructure Project
   💰 Est. Value: €1.5M
   ⏰ Deadline: 2 weeks
   
2. Government {prospect.sector} Services
   💰 Est. Value: €600,000
   ⏰ Deadline: 3 weeks
   
3. Municipal {prospect.sector} Contract
   💰 Est. Value: €400,000
   ⏰ Deadline: 4 weeks

These are just the ones I found today. There are probably 10+ more that I haven't seen yet.

Want to never miss another opportunity? TenderPulse monitors all EU procurement portals and sends you personalized alerts.

I can set up a free trial that shows you exactly which opportunities you're missing.

Just reply "TRIAL" and I'll get you access today.

Best regards,
Alex
TenderPulse

P.S. - New opportunities are published every day. Don't let them slip by."""

    async def send_follow_up_emails(self) -> int:
        """Send follow-up emails to prospects"""
        prospects = self.get_prospects_for_follow_up()
        sent_count = 0
        
        logger.info(f"Found {len(prospects)} prospects for follow-up")
        
        for prospect in prospects:
            try:
                # Determine sequence number based on last email
                last_email_sent = prospect.get('last_email_sent')
                if last_email_sent:
                    days_since_last = (datetime.now() - datetime.fromisoformat(last_email_sent)).days
                    sequence_number = min(days_since_last // 3, 4)  # Cap at sequence 4
                else:
                    sequence_number = 1
                
                # Generate follow-up email
                email_content = self.generate_follow_up_email(prospect, sequence_number)
                
                # Send email
                result = await self.email_sender.send_email(
                    to_email=prospect['email'],
                    subject=email_content['subject'],
                    body=email_content['body'],
                    html_body=email_content['html_body'],
                    tags=[f'followup_{sequence_number}', prospect['sector'].lower().replace(' ', '_')]
                )
                
                if result.get('status') == 'sent':
                    # Save email campaign
                    conn = sqlite3.connect(self.config.get('database.path'))
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO email_campaigns 
                        (prospect_id, campaign_name, subject, body, status, mailgun_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        prospect['id'], 
                        f'followup_sequence_{sequence_number}',
                        email_content['subject'],
                        email_content['body'],
                        'sent',
                        result.get('id'),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    
                    sent_count += 1
                    logger.info(f"Sent follow-up email to {prospect['email']}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error sending follow-up to {prospect.get('email', 'unknown')}: {e}")
        
        logger.info(f"Sent {sent_count} follow-up emails")
        return sent_count

class BackupSystem:
    """Automated backup and logging system"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_database_backup(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f"ted_prospects_{timestamp}.db")
        
        # Copy database file
        import shutil
        shutil.copy2(self.config.get('database.path'), backup_file)
        
        logger.info(f"Database backup created: {backup_file}")
        return backup_file
    
    def create_csv_backup(self) -> str:
        """Create CSV backup of all data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f"ted_data_{timestamp}.csv")
        
        conn = sqlite3.connect(self.config.get('database.path'))
        cursor = conn.cursor()
        
        # Export all prospects
        cursor.execute('SELECT * FROM prospects')
        columns = [description[0] for description in cursor.description]
        prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        import csv
        with open(backup_file, 'w', newline='', encoding='utf-8') as f:
            if prospects:
                writer = csv.DictWriter(f, fieldnames=prospects[0].keys())
                writer.writeheader()
                writer.writerows(prospects)
        
        conn.close()
        
        logger.info(f"CSV backup created: {backup_file}")
        return backup_file
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """Clean up old backup files"""
        import glob
        
        # Clean up database backups
        db_backups = glob.glob(os.path.join(self.backup_dir, "ted_prospects_*.db"))
        csv_backups = glob.glob(os.path.join(self.backup_dir, "ted_data_*.csv"))
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for backup_file in db_backups + csv_backups:
            file_time = datetime.fromtimestamp(os.path.getctime(backup_file))
            if file_time < cutoff_date:
                os.remove(backup_file)
                logger.info(f"Deleted old backup: {backup_file}")

class CRMIntegration:
    """CRM integration preparation"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.webhook_url = config.get('crm_webhook_url')
    
    def prepare_prospect_for_crm(self, prospect: Dict) -> Dict:
        """Prepare prospect data for CRM integration"""
        return {
            'company_name': prospect.get('company_name'),
            'email': prospect.get('email'),
            'contact_name': prospect.get('contact_name'),
            'phone': prospect.get('phone'),
            'website': prospect.get('website'),
            'country': prospect.get('country'),
            'sector': prospect.get('sector'),
            'status': prospect.get('status'),
            'pain_level': prospect.get('pain_level'),
            'lost_tender_value': prospect.get('lost_tender_value'),
            'buyer_name': prospect.get('buyer_name'),
            'created_at': prospect.get('created_at'),
            'source': 'TenderPulse_TED_Scraper',
            'tags': [prospect.get('sector'), prospect.get('country'), 'bid_loser']
        }
    
    async def sync_to_crm(self, prospect: Dict) -> bool:
        """Sync prospect to CRM via webhook"""
        if not self.webhook_url:
            logger.warning("CRM webhook URL not configured")
            return False
        
        try:
            import httpx
            crm_data = self.prepare_prospect_for_crm(prospect)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=crm_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Synced prospect {prospect['id']} to CRM")
                    return True
                else:
                    logger.error(f"CRM sync failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error syncing to CRM: {e}")
            return False

class AutomationOrchestrator:
    """Main automation orchestrator"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = ConfigManager(config_file)
        self.db = ProspectDatabase(self.config.get('database.path'))
        self.duplicate_detector = DuplicateDetector(self.config.get('database.path'))
        self.follow_up_sequencer = FollowUpSequencer(self.config, self.db)
        self.backup_system = BackupSystem(self.config)
        self.crm_integration = CRMIntegration(self.config)
        
        # Initialize automation config
        self.automation_config = AutomationConfig()
    
    async def run_daily_prospecting(self) -> Dict:
        """Run daily prospect finding with automation"""
        logger.info("🚀 Starting daily prospecting automation")
        
        results = {
            'prospects_found': 0,
            'emails_found': 0,
            'emails_sent': 0,
            'duplicates_skipped': 0,
            'follow_ups_sent': 0,
            'errors': []
        }
        
        try:
            # Step 1: Find new prospects
            logger.info("🎯 Finding new prospects from TED...")
            ted_finder = TEDProspectFinder(self.config)
            awards = await ted_finder.find_recent_awards()
            
            if not awards:
                logger.warning("No contract awards found")
                return results
            
            # Step 2: Extract prospects
            logger.info("🏢 Extracting prospect companies...")
            prospect_extractor = ProspectExtractor(self.config)
            all_prospects = prospect_extractor.extract_prospects_from_awards(awards)
            results['prospects_found'] = len(all_prospects)
            
            # Step 3: Duplicate detection and filtering
            logger.info("🔍 Checking for duplicates...")
            unique_prospects = []
            for prospect in all_prospects:
                # Check for exact duplicates
                existing_id = self.duplicate_detector.check_duplicate(prospect.__dict__)
                if existing_id:
                    results['duplicates_skipped'] += 1
                    logger.info(f"Skipped duplicate prospect: {prospect.company_name}")
                    continue
                
                # Check for similar prospects
                similar = self.duplicate_detector.find_similar_prospects(prospect.__dict__)
                if similar:
                    logger.info(f"Found {len(similar)} similar prospects for {prospect.company_name}")
                
                unique_prospects.append(prospect)
            
            # Step 4: Find email addresses
            logger.info("📧 Finding email addresses...")
            email_finder = EmailFinder(self.config)
            prospects_with_emails = []
            
            for prospect in unique_prospects:
                # Save prospect to database
                prospect_id = self.db.save_prospect(prospect)
                
                # Find email (Apollo.io primary, Hunter.io fallback)
                if self.config.get('api_keys.apollo_io') or self.config.get('api_keys.hunter_io'):
                    email_data = await email_finder.find_company_emails(prospect.company_name)
                    
                    if email_data and email_data.get('best_contact'):
                        contact = email_data['best_contact']
                        prospect.email = contact.get('value')
                        prospect.contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                        prospect.website = f"https://{email_data.get('domain', '')}"
                        prospect.status = 'email_found'
                        
                        prospects_with_emails.append(prospect)
                        
                        # Mark as processed for duplicate detection
                        self.duplicate_detector.mark_as_duplicate(prospect_id, prospect.__dict__)
                        
                        # Sync to CRM
                        await self.crm_integration.sync_to_crm(prospect.__dict__)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            results['emails_found'] = len(prospects_with_emails)
            
            # Step 5: Send initial outreach emails
            if prospects_with_emails:
                logger.info("📨 Sending initial outreach emails...")
                email_sender = EmailSender(self.config)
                template_generator = EmailTemplateGenerator(self.config)
                
                for prospect in prospects_with_emails:
                    try:
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
                            results['emails_sent'] += 1
                            prospect.status = 'contacted'
                            
                            # Update database
                            conn = sqlite3.connect(self.config.get('database.path'))
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE prospects 
                                SET status = 'contacted', updated_at = ?
                                WHERE id = ?
                            ''', (datetime.now().isoformat(), prospect_id))
                            conn.commit()
                            conn.close()
                        
                        # Rate limiting
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error sending email to {prospect.email}: {e}")
                        results['errors'].append(str(e))
            
            # Step 6: Send follow-up emails
            logger.info("📬 Sending follow-up emails...")
            follow_ups_sent = await self.follow_up_sequencer.send_follow_up_emails()
            results['follow_ups_sent'] = follow_ups_sent
            
            # Step 7: Create backup
            logger.info("💾 Creating backup...")
            self.backup_system.create_database_backup()
            self.backup_system.create_csv_backup()
            self.backup_system.cleanup_old_backups()
            
            logger.info("✅ Daily prospecting automation completed")
            
        except Exception as e:
            logger.error(f"Error in daily prospecting: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def schedule_daily_runs(self):
        """Schedule daily automation runs"""
        schedule.every().day.at(self.automation_config.daily_run_time).do(
            lambda: asyncio.run(self.run_daily_prospecting())
        )
        
        logger.info(f"📅 Scheduled daily runs at {self.automation_config.daily_run_time}")
    
    def run_scheduler(self):
        """Run the scheduler (blocking)"""
        self.schedule_daily_runs()
        
        logger.info("🔄 Starting automation scheduler...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

# CLI Commands
import click

@click.group()
def cli():
    """TenderPulse Automation System"""
    pass

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
def run_daily(config):
    """Run daily prospecting automation"""
    orchestrator = AutomationOrchestrator(config)
    results = asyncio.run(orchestrator.run_daily_prospecting())
    
    print("📊 Daily Automation Results:")
    print(f"🎯 Prospects found: {results['prospects_found']}")
    print(f"📧 Emails found: {results['emails_found']}")
    print(f"📨 Emails sent: {results['emails_sent']}")
    print(f"🔄 Follow-ups sent: {results['follow_ups_sent']}")
    print(f"🚫 Duplicates skipped: {results['duplicates_skipped']}")
    
    if results['errors']:
        print(f"❌ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   - {error}")

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
def start_scheduler(config):
    """Start the automation scheduler"""
    orchestrator = AutomationOrchestrator(config)
    orchestrator.run_scheduler()

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
def send_follow_ups(config):
    """Send follow-up emails to prospects"""
    orchestrator = AutomationOrchestrator(config)
    sent_count = asyncio.run(orchestrator.follow_up_sequencer.send_follow_up_emails())
    print(f"📬 Sent {sent_count} follow-up emails")

@cli.command()
@click.option('--config', default='config.json', help='Configuration file path')
def create_backup(config):
    """Create database and CSV backup"""
    orchestrator = AutomationOrchestrator(config)
    db_backup = orchestrator.backup_system.create_database_backup()
    csv_backup = orchestrator.backup_system.create_csv_backup()
    print(f"💾 Backups created:")
    print(f"   Database: {db_backup}")
    print(f"   CSV: {csv_backup}")

if __name__ == "__main__":
    cli()
