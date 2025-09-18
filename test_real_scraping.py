#!/usr/bin/env python3
"""
Test script for real data scraping from TED and BOAMP.
This will test our enhanced scrapers that connect to actual data sources.
"""

import asyncio
import asyncpg
from datetime import datetime, date
from typing import List, Dict, Any

# Import our real scrapers
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Database connection
DATABASE_URL = "postgresql://postgres:EgdluIbkCIAXlkAFozsnImoaeONMnAUw@switchyard.proxy.rlwy.net:37786/railway"

class RealDataTester:
    """Test real data scraping and storage."""
    
    def __init__(self):
        self.db_url = DATABASE_URL
    
    async def test_ted_real_scraping(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Test TED real data scraping."""
        print(f"🔍 Testing TED real data scraping (limit: {limit})...")
        
        try:
            # Import and test TED real scraper
            from backend.app.scrapers.real_data import TEDRealScraper
            
            async with TEDRealScraper() as scraper:
                tenders = await scraper.fetch_tenders(limit)
                
                print(f"✅ TED scraper returned {len(tenders)} tenders")
                
                if tenders:
                    sample = tenders[0]
                    print(f"📋 Sample TED tender:")
                    print(f"  • Ref: {sample['tender_ref']}")
                    print(f"  • Title: {sample['title'][:60]}...")
                    print(f"  • Country: {sample['buyer_country']}")
                    print(f"  • Date: {sample['publication_date']}")
                    print(f"  • Value: {sample.get('value_amount', 'N/A')} {sample.get('currency', '')}")
                
                return tenders
                
        except Exception as e:
            print(f"❌ TED real scraping failed: {e}")
            return []
    
    async def test_boamp_real_scraping(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Test BOAMP real data scraping."""
        print(f"\n🔍 Testing BOAMP real data scraping (limit: {limit})...")
        
        try:
            # Import and test BOAMP real scraper
            from backend.app.scrapers.real_data import BOAMPRealScraper
            
            async with BOAMPRealScraper() as scraper:
                tenders = await scraper.fetch_tenders(limit)
                
                print(f"✅ BOAMP scraper returned {len(tenders)} tenders")
                
                if tenders:
                    sample = tenders[0]
                    print(f"📋 Sample BOAMP tender:")
                    print(f"  • Ref: {sample['tender_ref']}")
                    print(f"  • Title: {sample['title'][:60]}...")
                    print(f"  • Buyer: {sample.get('buyer_name', 'N/A')}")
                    print(f"  • Date: {sample['publication_date']}")
                    print(f"  • Value: {sample.get('value_amount', 'N/A')} {sample.get('currency', '')}")
                
                return tenders
                
        except Exception as e:
            print(f"❌ BOAMP real scraping failed: {e}")
            return []
    
    async def test_additional_platforms(self):
        """Test additional platform discovery."""
        print(f"\n🌍 Testing additional procurement platforms...")
        
        try:
            from backend.app.scrapers.real_data import get_all_available_platforms
            
            platforms_info = await get_all_available_platforms()
            
            print(f"📊 Platform Coverage Summary:")
            print(f"  • Active platforms: {len(platforms_info['active_platforms'])}")
            print(f"  • Planned platforms: {len(platforms_info['planned_platforms'])}")
            print(f"  • Countries covered: {platforms_info['total_countries_covered']}")
            
            print(f"\n🚀 Integration Roadmap:")
            for phase, platforms in platforms_info['integration_roadmap'].items():
                print(f"  • {phase.replace('_', ' ').title()}: {', '.join(platforms)}")
            
            print(f"\n📋 Planned Platforms:")
            for platform in platforms_info['planned_platforms']:
                print(f"  • {platform['name']} ({platform['country']}) - Status: {platform['status']}")
                
        except Exception as e:
            print(f"❌ Additional platforms test failed: {e}")
    
    async def store_real_tenders(self, tenders: List[Dict[str, Any]]) -> int:
        """Store real tenders in database."""
        if not tenders:
            print("📝 No tenders to store")
            return 0
        
        print(f"\n📝 Storing {len(tenders)} real tenders in database...")
        
        conn = await asyncpg.connect(self.db_url)
        try:
            stored_count = 0
            for tender in tenders:
                try:
                    # Convert date strings to date objects if needed
                    pub_date = tender['publication_date']
                    if isinstance(pub_date, str):
                        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date()
                    
                    deadline_date = tender.get('deadline_date')
                    if isinstance(deadline_date, str):
                        deadline_date = datetime.strptime(deadline_date, '%Y-%m-%d').date()
                    elif deadline_date is None:
                        deadline_date = None
                    
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
                        tender.get('summary'),
                        pub_date,
                        deadline_date,
                        tender.get('cpv_codes', []),
                        tender.get('buyer_name'),
                        tender['buyer_country'],
                        float(tender['value_amount']) if tender.get('value_amount') else None,
                        tender.get('currency'),
                        tender['url']
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"⚠️  Error storing tender {tender['tender_ref']}: {e}")
            
            print(f"✅ Successfully stored {stored_count} real tenders")
            return stored_count
            
        finally:
            await conn.close()
    
    async def verify_data_quality(self):
        """Verify the quality of scraped data."""
        print(f"\n🔍 Verifying data quality...")
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Get data quality metrics
            total_tenders = await conn.fetchval("SELECT COUNT(*) FROM tenders")
            
            # Check for real vs sample data
            real_ted_count = await conn.fetchval("""
                SELECT COUNT(*) FROM tenders 
                WHERE source = 'TED' AND tender_ref LIKE 'TED-%' 
                AND NOT tender_ref LIKE 'TED-00000%'
            """)
            
            real_boamp_count = await conn.fetchval("""
                SELECT COUNT(*) FROM tenders 
                WHERE source = 'BOAMP_FR' AND tender_ref LIKE 'BOAMP-%'
                AND NOT tender_ref LIKE 'BOAMP-00000%'
            """)
            
            # Check data completeness
            tenders_with_values = await conn.fetchval("""
                SELECT COUNT(*) FROM tenders WHERE value_amount IS NOT NULL
            """)
            
            tenders_with_deadlines = await conn.fetchval("""
                SELECT COUNT(*) FROM tenders WHERE deadline_date IS NOT NULL
            """)
            
            tenders_with_cpv = await conn.fetchval("""
                SELECT COUNT(*) FROM tenders WHERE array_length(cpv_codes, 1) > 0
            """)
            
            print(f"📊 Data Quality Report:")
            print(f"  • Total tenders: {total_tenders}")
            print(f"  • Real TED tenders: {real_ted_count}")
            print(f"  • Real BOAMP tenders: {real_boamp_count}")
            print(f"  • Tenders with values: {tenders_with_values} ({tenders_with_values/total_tenders*100:.1f}%)")
            print(f"  • Tenders with deadlines: {tenders_with_deadlines} ({tenders_with_deadlines/total_tenders*100:.1f}%)")
            print(f"  • Tenders with CPV codes: {tenders_with_cpv} ({tenders_with_cpv/total_tenders*100:.1f}%)")
            
            # Show recent real data samples
            real_samples = await conn.fetch("""
                SELECT tender_ref, title, source, buyer_country, publication_date, value_amount, currency
                FROM tenders 
                WHERE (source = 'TED' AND NOT tender_ref LIKE 'TED-00000%')
                   OR (source = 'BOAMP_FR' AND NOT tender_ref LIKE 'BOAMP-00000%')
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            if real_samples:
                print(f"\n📋 Recent Real Data Samples:")
                for sample in real_samples:
                    value_str = f"{sample['value_amount']:,.0f} {sample['currency']}" if sample['value_amount'] else "N/A"
                    print(f"  • {sample['tender_ref']}: {sample['title'][:40]}... ({sample['source']}, {sample['buyer_country']}, {value_str})")
            
        finally:
            await conn.close()
    
    async def run_full_test(self):
        """Run the complete real data scraping test."""
        print("🚀 Starting Real Data Scraping Test")
        print("=" * 60)
        
        # Test TED real scraping
        ted_tenders = await self.test_ted_real_scraping(limit=15)
        
        # Test BOAMP real scraping  
        boamp_tenders = await self.test_boamp_real_scraping(limit=10)
        
        # Test additional platforms
        await self.test_additional_platforms()
        
        # Store all real tenders
        all_tenders = ted_tenders + boamp_tenders
        if all_tenders:
            stored_count = await self.store_real_tenders(all_tenders)
            
            # Verify data quality
            await self.verify_data_quality()
        
        print(f"\n🎉 Real Data Scraping Test Completed!")
        print(f"📊 Summary:")
        print(f"  • TED tenders scraped: {len(ted_tenders)}")
        print(f"  • BOAMP tenders scraped: {len(boamp_tenders)}")
        print(f"  • Total real tenders: {len(all_tenders)}")
        
        print(f"\n🔗 Test the updated API:")
        print(f"  • Backend: https://procurement-copilot-production.up.railway.app/api/v1/docs")
        print(f"  • Tenders: https://procurement-copilot-production.up.railway.app/api/v1/tenders/tenders")
        print(f"  • Stats: https://procurement-copilot-production.up.railway.app/api/v1/tenders/tenders/stats/summary")


async def main():
    """Main function."""
    tester = RealDataTester()
    await tester.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())
