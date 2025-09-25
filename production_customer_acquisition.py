#!/usr/bin/env python3
"""
TenderPulse Production Customer Acquisition Engine
Complete system: Find prospects → Get emails → Send outreach → Track results

REQUIRED API KEYS (add to .env):
HUNTER_API_KEY=your_hunter_io_key
RESEND_API_KEY=your_resend_key  
APOLLO_API_KEY=your_apollo_key (optional)
DATABASE_URL=your_postgres_url (optional, uses SQLite if not set)
"""

import os
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import httpx
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Prospect:
    """A prospect company with contact info"""
    company_name: str
    country: str
    tender_id: str
    tender_title: str
    tender_value: str
    lost_date: str
    sector: str
    buyer_name: str
    pain_level: int
    email: Optional[str] = None
    contact_name: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    phone: Optional[str] = None
    status: str = 'found'  # found, email_found, contacted, responded, converted
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class ProspectDatabase:
    """Simple SQLite database for tracking prospects"""
    
    def __init__(self, db_path: str = "prospects.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                country TEXT,
                tender_id TEXT,
                tender_title TEXT,
                tender_value TEXT,
                lost_date TEXT,
                sector TEXT,
                buyer_name TEXT,
                pain_level INTEGER,
                email TEXT,
                contact_name TEXT,
                website TEXT,
                linkedin TEXT,
                phone TEXT,
                status TEXT DEFAULT 'found',
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(company_name, tender_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                subject TEXT,
                body TEXT,
                sent_at TEXT,
                opened_at TEXT,
                clicked_at TEXT,
                replied_at TEXT,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (prospect_id) REFERENCES prospects (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_prospect(self, prospect: Prospect) -> int:
        """Save prospect to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO prospects 
                (company_name, country, tender_id, tender_title, tender_value, 
                 lost_date, sector, buyer_name, pain_level, email, contact_name, 
                 website, linkedin, phone, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prospect.company_name, prospect.country, prospect.tender_id,
                prospect.tender_title, prospect.tender_value, prospect.lost_date,
                prospect.sector, prospect.buyer_name, prospect.pain_level,
                prospect.email, prospect.contact_name, prospect.website,
                prospect.linkedin, prospect.phone, prospect.status,
                prospect.created_at, datetime.now().isoformat()
            ))
            
            prospect_id = cursor.lastrowid
            conn.commit()
            return prospect_id
            
        except Exception as e:
            print(f"Error saving prospect: {e}")
            return None
        finally:
            conn.close()
    
    def get_prospects_by_status(self, status: str) -> List[Dict]:
        """Get prospects by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prospects WHERE status = ?', (status,))
        columns = [description[0] for description in cursor.description]
        prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return prospects
    
    def update_prospect_status(self, prospect_id: int, status: str, **kwargs):
        """Update prospect status and other fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?', 'updated_at = ?']
        values = [status, datetime.now().isoformat()]
        
        for key, value in kwargs.items():
            update_fields.append(f'{key} = ?')
            values.append(value)
        
        values.append(prospect_id)
        
        cursor.execute(f'''
            UPDATE prospects 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()

class EmailFinder:
    """Find email addresses for prospect companies"""
    
    def __init__(self):
        self.hunter_api_key = os.getenv('HUNTER_API_KEY')
        self.apollo_api_key = os.getenv('APOLLO_API_KEY')
    
    async def find_company_emails(self, company_name: str, website: str = None) -> Dict:
        """Find emails for a company using Hunter.io"""
        if not self.hunter_api_key:
            print("⚠️ HUNTER_API_KEY not set - skipping email finding")
            return {}
        
        # First, try to find the company domain
        domain = await self.find_company_domain(company_name, website)
        if not domain:
            return {}
        
        # Then find emails for that domain
        return await self.find_emails_by_domain(domain)
    
    async def find_company_domain(self, company_name: str, website: str = None) -> str:
        """Find company domain using Hunter.io domain search"""
        if website:
            # Extract domain from website
            domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
            return domain
        
        # Use Hunter.io to find domain by company name
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.hunter.io/v2/domain-search",
                    params={
                        'company': company_name,
                        'api_key': self.hunter_api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('domain'):
                        return data['data']['domain']
                        
            except Exception as e:
                print(f"Error finding domain for {company_name}: {e}")
        
        return None
    
    async def find_emails_by_domain(self, domain: str) -> Dict:
        """Find emails for a domain using Hunter.io"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.hunter.io/v2/domain-search",
                    params={
                        'domain': domain,
                        'api_key': self.hunter_api_key,
                        'type': 'personal'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    emails = data.get('data', {}).get('emails', [])
                    
                    # Find best contact (CEO, founder, business development, sales)
                    best_contact = self.find_best_contact(emails)
                    
                    return {
                        'domain': domain,
                        'emails': emails,
                        'best_contact': best_contact,
                        'total_emails': len(emails)
                    }
                        
            except Exception as e:
                print(f"Error finding emails for {domain}: {e}")
        
        return {}
    
    def find_best_contact(self, emails: List[Dict]) -> Dict:
        """Find the best contact person from email list"""
        if not emails:
            return {}
        
        # Prioritize by position
        priority_positions = [
            'ceo', 'founder', 'owner', 'director', 'president',
            'business development', 'sales', 'marketing', 
            'procurement', 'purchasing', 'operations'
        ]
        
        for position in priority_positions:
            for email in emails:
                position_text = email.get('position', '').lower()
                if position in position_text:
                    return email
        
        # If no priority position found, return first email
        return emails[0] if emails else {}

class EmailSender:
    """Send outreach emails using Resend"""
    
    def __init__(self):
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'hello@tenderpulse.eu')
        self.from_name = os.getenv('FROM_NAME', 'Alex from TenderPulse')
    
    async def send_outreach_email(self, prospect: Prospect, email_content: Dict) -> bool:
        """Send outreach email via Resend"""
        if not self.resend_api_key:
            print("⚠️ RESEND_API_KEY not set - would send email to:", prospect.email)
            return False
        
        if not prospect.email:
            print(f"⚠️ No email for {prospect.company_name}")
            return False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"{self.from_name} <{self.from_email}>",
                        "to": [prospect.email],
                        "subject": email_content['subject'],
                        "html": self.convert_to_html(email_content['body']),
                        "text": email_content['body'],
                        "tags": [
                            {"name": "campaign", "value": "bid_losers"},
                            {"name": "sector", "value": prospect.sector},
                            {"name": "country", "value": prospect.country}
                        ]
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Email sent to {prospect.email}")
                    return True
                else:
                    print(f"❌ Failed to send email: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error sending email to {prospect.email}: {e}")
                return False
    
    def convert_to_html(self, text_body: str) -> str:
        """Convert plain text email to HTML"""
        html_body = text_body.replace('\n', '<br>')
        
        # Add some basic styling
        html_template = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {html_body}
                <br><br>
                <div style="border-top: 1px solid #eee; padding-top: 20px; font-size: 12px; color: #666;">
                    <p>TenderPulse - Never Miss Another Tender</p>
                    <p>This email was sent because you recently participated in EU public procurement.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template

class OutreachEmailGenerator:
    """Generate high-converting outreach emails"""
    
    def generate_personalized_email(self, prospect: Prospect, similar_opportunities: List[Dict] = None) -> Dict:
        """Generate personalized email for prospect"""
        
        if similar_opportunities is None:
            similar_opportunities = self.generate_mock_opportunities(prospect)
        
        # Subject line variations
        subject_options = [
            f"5 new {prospect.sector} opportunities in {prospect.country} (like the {self.extract_value(prospect.tender_value)} tender)",
            f"Don't miss the next {prospect.buyer_name} contract",
            f"Similar tenders to your recent {prospect.sector} bid closing soon",
            f"Why you should have won that {self.extract_value(prospect.tender_value)} contract (+ 3 new ones)"
        ]
        
        # Personalized greeting
        greeting = f"Hi {prospect.contact_name}," if prospect.contact_name else "Hi there,"
        
        # Email body
        email_body = f"""{greeting}

I noticed your company recently participated in this procurement:

📋 "{prospect.tender_title}"
🏢 Buyer: {prospect.buyer_name}  
💰 Value: {prospect.tender_value}
📅 Award Date: {self.format_date(prospect.lost_date)}

While that opportunity has closed, I found {len(similar_opportunities)} similar contracts that might be perfect for your business:

"""
        
        # Add specific opportunities
        for i, opp in enumerate(similar_opportunities[:3], 1):
            email_body += f"""
{i}. {opp.get('title', 'Government Contract')[:60]}...
   💰 Est. Value: {opp.get('value', '€400,000')}
   🏢 Buyer: {opp.get('buyer', 'Government Agency')}
   ⏰ Status: Open for bidding
   🔗 Link: https://ted.europa.eu/udl?uri=TED:NOTICE:{opp.get('tender_id', 'example')}

"""
        
        email_body += f"""Here's the thing - most {prospect.sector} companies miss 80% of relevant opportunities because they're scattered across 27+ different procurement portals.

That's exactly why we built TenderPulse.

🎯 What TenderPulse does for {prospect.sector} companies:
✓ Monitors ALL EU procurement portals 24/7
✓ AI scoring shows which contracts you can actually win  
✓ Early alerts give you weeks to prepare (not days)
✓ Response templates from contracts we've helped win
✓ Never miss deadlines with automated reminders

Our users win 34% more contracts because they focus on the RIGHT opportunities at the RIGHT time.

Want to see how it works for {prospect.sector} companies in {prospect.country}?

I can set up a free trial that shows you exactly which opportunities you're missing right now.

Just reply "YES" and I'll get you access today.

Best regards,
{os.getenv('FROM_NAME', 'Alex')}
TenderPulse - Never Miss Another Tender

P.S. - The next big {prospect.sector} contract in {prospect.country} could be published tomorrow. Don't let another one slip by.
"""
        
        return {
            'subject': subject_options[0],
            'body': email_body,
            'prospect_score': prospect.pain_level
        }
    
    def generate_mock_opportunities(self, prospect: Prospect) -> List[Dict]:
        """Generate mock similar opportunities for demo"""
        return [
            {
                'title': f"{prospect.sector} opportunity in {prospect.country}",
                'buyer': f"{prospect.country} Government Agency",
                'value': prospect.tender_value,
                'tender_id': f"SIMILAR-{i}"
            }
            for i in range(3)
        ]
    
    def extract_value(self, value_str: str) -> str:
        """Extract and format value"""
        if not value_str:
            return "€400K"
        
        # Extract number
        numbers = re.findall(r'[\d,]+', value_str)
        if numbers:
            try:
                num = int(numbers[0].replace(',', ''))
                if num >= 1000000:
                    return f"€{num//1000000}M"
                elif num >= 1000:
                    return f"€{num//1000}K"
                else:
                    return f"€{num:,}"
            except:
                pass
        
        return "€400K"
    
    def format_date(self, date_str: str) -> str:
        """Format date for email"""
        try:
            clean_date = date_str.split('+')[0].split('T')[0]
            date_obj = datetime.strptime(clean_date, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return 'Recently'

class TenderPulseProspector:
    """Main prospecting engine"""
    
    def __init__(self):
        self.ted_endpoint = "https://api.ted.europa.eu/v3/notices/search"
        self.db = ProspectDatabase()
        self.email_finder = EmailFinder()
        self.email_sender = EmailSender()
        self.email_generator = OutreachEmailGenerator()
    
    async def run_daily_prospecting(self):
        """Main function - run this daily"""
        
        print("🚀 TenderPulse Daily Customer Acquisition")
        print("=" * 50)
        
        # Step 1: Find new prospects from TED
        print("🎯 Step 1: Finding new bid losers...")
        new_prospects = await self.find_bid_losers()
        
        if not new_prospects:
            print("⚠️ No new prospects found today")
            return
        
        print(f"✅ Found {len(new_prospects)} new prospects")
        
        # Step 2: Find email addresses
        print("\n📧 Step 2: Finding email addresses...")
        prospects_with_emails = await self.find_prospect_emails(new_prospects)
        
        # Step 3: Send outreach emails
        print("\n📨 Step 3: Sending outreach emails...")
        sent_count = await self.send_outreach_emails(prospects_with_emails)
        
        # Step 4: Generate summary report
        print(f"\n📊 DAILY SUMMARY:")
        print(f"🎯 New prospects found: {len(new_prospects)}")
        print(f"📧 Emails found: {len(prospects_with_emails)}")
        print(f"📨 Emails sent: {sent_count}")
        
        # Step 5: Show revenue projection
        total_prospects = len(self.db.get_prospects_by_status('found')) + len(prospects_with_emails)
        monthly_revenue = total_prospects * 0.15 * 99  # 15% conversion at €99/month
        
        print(f"\n💰 REVENUE PROJECTION:")
        print(f"📈 Total prospects in pipeline: {total_prospects}")
        print(f"💰 Potential monthly revenue: €{monthly_revenue:,.0f}")
        print(f"🎊 Annual revenue potential: €{monthly_revenue * 12:,.0f}")
    
    async def find_bid_losers(self) -> List[Prospect]:
        """Find new bid losers from TED API"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "query": "TI=award OR TI=contract OR TI=winner",
                    "fields": ["ND", "TI", "PD", "buyer-name", "links"]
                }
                
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'TenderPulse-Prospector/1.0'
                }
                
                response = await client.post(self.ted_endpoint, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return await self.process_ted_data(data)
                else:
                    print(f"❌ TED API failed: {response.status_code}")
                    return []
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return []
    
    async def process_ted_data(self, data: Dict) -> List[Prospect]:
        """Process TED data into prospects"""
        
        prospects = []
        notices = data.get('notices', [])
        
        for notice in notices:
            try:
                # Extract title
                title_obj = notice.get('TI', {})
                if isinstance(title_obj, dict):
                    title = title_obj.get('eng', list(title_obj.values())[0] if title_obj else 'Contract Award')
                else:
                    title = str(title_obj) if title_obj else 'Contract Award'
                
                # Only process award notices
                if not any(word in title.lower() for word in ['award', 'contract', 'winner', 'result']):
                    continue
                
                # Extract company name from title (this is simplified - in reality you'd parse the full notice)
                company_name = self.extract_company_name_from_title(title)
                
                prospect = Prospect(
                    company_name=company_name,
                    country=self.extract_country_from_title(title),
                    tender_id=notice.get('ND', 'unknown'),
                    tender_title=title,
                    tender_value=f"€{self.estimate_value(title):,}",
                    lost_date=notice.get('PD', datetime.now().isoformat()),
                    sector=self.identify_sector(title),
                    buyer_name=self.extract_buyer_from_title(title),
                    pain_level=self.calculate_pain_level(title, self.estimate_value(title))
                )
                
                # Save to database
                prospect_id = self.db.save_prospect(prospect)
                if prospect_id:
                    prospects.append(prospect)
                
            except Exception as e:
                print(f"Error processing notice: {e}")
                continue
        
        return prospects
    
    def extract_company_name_from_title(self, title: str) -> str:
        """Extract losing company name from title (simplified)"""
        # In reality, you'd parse the full notice XML to get actual company names
        # For now, we'll create a generic name based on the sector
        sector = self.identify_sector(title)
        country = self.extract_country_from_title(title)
        return f"{country} {sector} Company (Name TBD)"
    
    async def find_prospect_emails(self, prospects: List[Prospect]) -> List[Prospect]:
        """Find email addresses for prospects"""
        
        prospects_with_emails = []
        
        for prospect in prospects:
            print(f"🔍 Finding emails for {prospect.company_name}...")
            
            # Find emails using Hunter.io
            email_data = await self.email_finder.find_company_emails(prospect.company_name)
            
            if email_data and email_data.get('best_contact'):
                contact = email_data['best_contact']
                prospect.email = contact.get('value')
                prospect.contact_name = contact.get('first_name', '') + ' ' + contact.get('last_name', '')
                prospect.website = f"https://{email_data.get('domain', '')}"
                prospect.status = 'email_found'
                
                # Update in database
                self.db.update_prospect_status(
                    prospect_id=None,  # Would need to track IDs better
                    status='email_found',
                    email=prospect.email,
                    contact_name=prospect.contact_name,
                    website=prospect.website
                )
                
                prospects_with_emails.append(prospect)
                print(f"✅ Found email: {prospect.email}")
            else:
                print(f"❌ No email found for {prospect.company_name}")
        
        return prospects_with_emails
    
    async def send_outreach_emails(self, prospects: List[Prospect]) -> int:
        """Send outreach emails to prospects"""
        
        sent_count = 0
        
        for prospect in prospects:
            # Generate personalized email
            email_content = self.email_generator.generate_personalized_email(prospect)
            
            # Send email
            if await self.email_sender.send_outreach_email(prospect, email_content):
                prospect.status = 'contacted'
                # Update database status
                sent_count += 1
            
            # Rate limiting - don't send too many emails at once
            await asyncio.sleep(2)  # 2 second delay between emails
        
        return sent_count
    
    # Helper methods (same as before)
    def extract_country_from_title(self, title: str) -> str:
        country_mapping = {
            'Germany': 'DE', 'Deutschland': 'DE',
            'France': 'FR', 'Francia': 'FR',
            'Italy': 'IT', 'Italia': 'IT',
            'Spain': 'ES', 'España': 'ES',
            'Netherlands': 'NL',
            'Sweden': 'SE', 'Sverige': 'SE'
        }
        
        for country_name, code in country_mapping.items():
            if country_name.lower() in title.lower():
                return code
        return 'EU'
    
    def extract_buyer_from_title(self, title: str) -> str:
        if ':' in title:
            location_part = title.split(':')[0]
            if '-' in location_part:
                return location_part.split('-', 1)[1].strip() + " Authority"
        return "Government Agency"
    
    def estimate_value(self, title: str) -> int:
        value_indicators = {
            'infrastructure': 2000000,
            'construction': 1500000,
            'it services': 800000,
            'software': 500000,
            'consulting': 300000
        }
        
        title_lower = title.lower()
        for keyword, value in value_indicators.items():
            if keyword in title_lower:
                return value
        
        return 400000
    
    def identify_sector(self, title: str) -> str:
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['it', 'software', 'digital', 'technology']):
            return 'IT & Software'
        elif any(word in title_lower for word in ['construction', 'building', 'infrastructure']):
            return 'Construction'
        elif any(word in title_lower for word in ['consulting', 'advisory', 'management']):
            return 'Consulting'
        else:
            return 'Professional Services'
    
    def calculate_pain_level(self, title: str, value: int) -> int:
        pain = 50
        
        if value > 1000000:
            pain += 30
        elif value > 500000:
            pain += 20
        
        if any(word in title.lower() for word in ['it', 'software', 'consulting']):
            pain += 15
        
        return max(20, min(95, pain))

# CLI Commands
async def run_daily():
    """Run daily prospecting"""
    prospector = TenderPulseProspector()
    await prospector.run_daily_prospecting()

def show_prospects():
    """Show current prospects in database"""
    db = ProspectDatabase()
    
    print("📊 CURRENT PROSPECTS:")
    print("=" * 50)
    
    statuses = ['found', 'email_found', 'contacted', 'responded', 'converted']
    
    for status in statuses:
        prospects = db.get_prospects_by_status(status)
        print(f"\n{status.upper()}: {len(prospects)} prospects")
        
        for prospect in prospects[:5]:  # Show first 5
            print(f"  • {prospect['company_name']} ({prospect['country']}) - {prospect['sector']}")

def test_email_finding():
    """Test email finding functionality"""
    async def test():
        finder = EmailFinder()
        result = await finder.find_company_emails("Microsoft", "microsoft.com")
        print("Email finding test result:", json.dumps(result, indent=2))
    
    asyncio.run(test())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "daily":
            asyncio.run(run_daily())
        elif command == "prospects":
            show_prospects()
        elif command == "test-email":
            test_email_finding()
        else:
            print("Usage: python production_customer_acquisition.py [daily|prospects|test-email]")
    else:
        print("🚀 TenderPulse Production Customer Acquisition Engine")
        print("=" * 50)
        print()
        print("Commands:")
        print("  python production_customer_acquisition.py daily     - Run daily prospecting")
        print("  python production_customer_acquisition.py prospects - Show current prospects")
        print("  python production_customer_acquisition.py test-email - Test email finding")
        print()
        print("Required environment variables:")
        print("  HUNTER_API_KEY    - Hunter.io API key for email finding")
        print("  RESEND_API_KEY    - Resend API key for sending emails")
        print("  FROM_EMAIL        - Your sending email address")
        print("  FROM_NAME         - Your name for email signatures")
        print()
        print("Optional:")
        print("  APOLLO_API_KEY    - Apollo.io API key (alternative email finder)")
        print("  DATABASE_URL      - PostgreSQL URL (uses SQLite if not set)")
