#!/usr/bin/env python3
"""
Script to trigger data scraping via direct database connection.
This bypasses the need for local CLI setup.
"""

import asyncio
import asyncpg
import httpx
import json
from datetime import datetime, date
from typing import List, Dict, Any
import re

# Database connection
DATABASE_URL = "postgresql://postgres:EgdluIbkCIAXlkAFozsnImoaeONMnAUw@switchyard.proxy.rlwy.net:37786/railway"

class TenderScraper:
    """Simple tender scraper for testing."""
    
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def scrape_ted_sample(self, limit: int = 10) -> List[Dict[Any, Any]]:
        """Scrape a sample of tenders from TED (European procurement)."""
        print(f"🔍 Scraping {limit} sample tenders from TED...")
        
        tenders = []
        
        # Sample TED data (in real implementation, this would call TED API)
        sample_tenders = [
            {
                "tender_ref": f"TED-{i:06d}-2025",
                "source": "TED", 
                "title": f"Construction Services Contract #{i}",
                "summary": f"Public procurement for construction and infrastructure services in European region #{i}",
                "publication_date": "2025-09-18",
                "deadline_date": "2025-10-18",
                "cpv_codes": ["45000000", "45200000"],  # Construction codes
                "buyer_name": f"City Council #{i}",
                "buyer_country": "FR" if i % 2 == 0 else "DE",
                "value_amount": f"{100000 + (i * 50000)}",
                "currency": "EUR",
                "url": f"https://ted.europa.eu/tender-{i}"
            }
            for i in range(1, limit + 1)
        ]
        
        return sample_tenders
    
    async def scrape_boamp_sample(self, limit: int = 10) -> List[Dict[Any, Any]]:
        """Scrape a sample of tenders from BOAMP (French procurement).""" 
        print(f"🔍 Scraping {limit} sample tenders from BOAMP...")
        
        sample_tenders = [
            {
                "tender_ref": f"BOAMP-{i:06d}-2025",
                "source": "BOAMP_FR",
                "title": f"Services Contract France #{i}",
                "summary": f"French public procurement for professional services #{i}",
                "publication_date": "2025-09-18", 
                "deadline_date": "2025-11-18",
                "cpv_codes": ["72000000", "73000000"],  # IT services codes
                "buyer_name": f"Prefecture #{i}",
                "buyer_country": "FR",
                "value_amount": f"{50000 + (i * 25000)}",
                "currency": "EUR", 
                "url": f"https://boamp.fr/tender-{i}"
            }
            for i in range(1, limit + 1)
        ]
        
        return sample_tenders
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()

async def store_tenders(tenders: List[Dict[Any, Any]]):
    """Store tenders in the database."""
    if not tenders:
        print("📝 No tenders to store")
        return
    
    print(f"📝 Storing {len(tenders)} tenders in database...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        stored_count = 0
        for tender in tenders:
            try:
                # Convert date strings to date objects
                pub_date = datetime.strptime(tender['publication_date'], '%Y-%m-%d').date()
                deadline_date = datetime.strptime(tender['deadline_date'], '%Y-%m-%d').date() if tender.get('deadline_date') else None
                
                await conn.execute("""
                    INSERT INTO tenders (
                        tender_ref, source, title, summary, publication_date, 
                        deadline_date, cpv_codes, buyer_name, buyer_country,
                        value_amount, currency, url
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (tender_ref) DO NOTHING
                """, 
                    tender['tender_ref'],
                    tender['source'],
                    tender['title'], 
                    tender['summary'],
                    pub_date,
                    deadline_date,
                    tender['cpv_codes'],
                    tender['buyer_name'],
                    tender['buyer_country'],
                    float(tender['value_amount']) if tender['value_amount'] else None,
                    tender['currency'],
                    tender['url']
                )
                stored_count += 1
            except Exception as e:
                print(f"⚠️  Error storing tender {tender['tender_ref']}: {e}")
        
        print(f"✅ Successfully stored {stored_count} tenders")
        
    finally:
        await conn.close()

async def create_demo_user():
    """Create a demo user for testing."""
    print("👤 Creating demo user...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user_id = await conn.fetchval("""
            INSERT INTO users (email, full_name, is_active)
            VALUES ('demo@procurement-copilot.com', 'Demo User', true)
            ON CONFLICT (email) DO UPDATE SET updated_at = NOW()
            RETURNING id
        """)
        
        print(f"✅ Demo user created/updated: {user_id}")
        return user_id
        
    finally:
        await conn.close()

async def create_demo_filters(user_id: str):
    """Create demo saved filters."""
    print("📋 Creating demo saved filters...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        filters = [
            {
                "name": "Construction & Infrastructure",
                "keywords": ["construction", "infrastructure", "building"],
                "cpv_codes": ["45000000", "45200000", "45300000"],
                "countries": ["FR", "DE", "ES"],
                "min_value": 100000
            },
            {
                "name": "IT Services & Software",
                "keywords": ["software", "IT", "development", "digital"],
                "cpv_codes": ["72000000", "73000000", "48000000"],
                "countries": ["FR", "DE", "NL"],
                "min_value": 50000
            },
            {
                "name": "Consulting Services",
                "keywords": ["consulting", "advisory", "management"],
                "cpv_codes": ["79000000", "73000000"],
                "countries": ["FR", "BE", "LU"],
                "min_value": 25000
            }
        ]
        
        for filter_data in filters:
            await conn.execute("""
                INSERT INTO saved_filters (
                    user_id, name, keywords, cpv_codes, countries, min_value, notify_frequency
                ) VALUES ($1, $2, $3, $4, $5, $6, 'daily')
                ON CONFLICT DO NOTHING
            """,
                user_id,
                filter_data["name"],
                filter_data["keywords"],
                filter_data["cpv_codes"], 
                filter_data["countries"],
                filter_data["min_value"]
            )
        
        print(f"✅ Created {len(filters)} demo filters")
        
    finally:
        await conn.close()

async def check_data():
    """Check what data we have in the database."""
    print("📊 Checking database contents...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Count tenders
        tender_count = await conn.fetchval("SELECT COUNT(*) FROM tenders")
        print(f"📄 Tenders: {tender_count}")
        
        # Count users  
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"👥 Users: {user_count}")
        
        # Count filters
        filter_count = await conn.fetchval("SELECT COUNT(*) FROM saved_filters")
        print(f"📋 Saved Filters: {filter_count}")
        
        if tender_count > 0:
            # Show sample tenders
            sample_tenders = await conn.fetch("""
                SELECT tender_ref, title, source, buyer_country, value_amount, currency
                FROM tenders 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            
            print("\n📋 Sample tenders:")
            for tender in sample_tenders:
                value_str = f"{tender['value_amount']:,.0f} {tender['currency']}" if tender['value_amount'] else "N/A"
                print(f"  • {tender['tender_ref']}: {tender['title'][:50]}... ({tender['source']}, {tender['buyer_country']}, {value_str})")
        
    finally:
        await conn.close()

async def main():
    """Main function to run the scraping pipeline."""
    print("🚀 Starting Procurement Copilot Data Pipeline")
    print("=" * 50)
    
    scraper = TenderScraper()
    
    try:
        # Scrape sample data
        ted_tenders = await scraper.scrape_ted_sample(limit=15)
        boamp_tenders = await scraper.scrape_boamp_sample(limit=10)
        
        all_tenders = ted_tenders + boamp_tenders
        print(f"\n📥 Scraped {len(all_tenders)} total tenders")
        
        # Store in database
        await store_tenders(all_tenders)
        
        # Create demo user and filters
        user_id = await create_demo_user()
        await create_demo_filters(user_id)
        
        # Check final state
        print("\n" + "=" * 50)
        await check_data()
        
        print("\n🎉 Data pipeline completed successfully!")
        print("🔗 Test the API: https://procurement-copilot-production.up.railway.app/api/v1/docs")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
