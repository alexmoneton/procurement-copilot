#!/usr/bin/env python3
"""
Simple Funnel Test - Test core functionality step by step
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_ted_prospect_finder import (
    TEDProspectFinder, 
    EmailFinder, 
    ConfigManager,
    ProspectDatabase,
    ProspectExtractor
)

async def test_simple_funnel():
    """Test the core funnel components"""
    
    print("🚀 TESTING CORE FUNNEL COMPONENTS")
    print("=" * 50)
    
    # Initialize components
    config = ConfigManager()
    db = ProspectDatabase(config.get('database.path', 'ted_prospects.db'))
    
    print("\n✅ 1. TED API - Finding Recent Awards")
    print("-" * 40)
    
    try:
        ted_finder = TEDProspectFinder(config)
        awards = await ted_finder.find_recent_awards()
        
        if awards:
            print(f"✅ Found {len(awards)} contract awards")
            print(f"   Sample: {awards[0].title[:60]}...")
            
            # Test prospect extraction
            print("\n✅ 2. Prospect Extraction")
            print("-" * 40)
            
            extractor = ProspectExtractor(config)
            prospects = extractor.extract_prospects_from_awards(awards[:2])  # Just 2 for testing
            
            if prospects:
                print(f"✅ Extracted {len(prospects)} prospects")
                for i, prospect in enumerate(prospects):
                    print(f"   {i+1}. {prospect.company_name} ({prospect.country})")
                
                # Test email finding on first prospect
                print("\n✅ 3. Email Finding")
                print("-" * 40)
                
                email_finder = EmailFinder(config)
                first_prospect = prospects[0]
                
                print(f"🔍 Finding emails for: {first_prospect.company_name}")
                email_result = await email_finder.find_company_emails(first_prospect.company_name)
                
                if email_result and email_result.get('emails'):
                    print(f"✅ Found {len(email_result['emails'])} emails")
                    first_prospect.email = email_result['emails'][0]
                    first_prospect.status = 'email_found'
                else:
                    print("⚠️ No emails found (normal for some companies)")
                
                # Save to database
                print("\n✅ 4. Database Storage")
                print("-" * 40)
                
                for prospect in prospects:
                    prospect_id = db.save_prospect(prospect)
                    print(f"✅ Saved prospect: {prospect.company_name} (ID: {prospect_id})")
                
                # Check final stats
                stats = db.get_stats()
                print(f"\n📊 Final Database Stats:")
                print(f"   Total prospects: {stats.get('total_prospects', 0)}")
                print(f"   By status: {stats.get('prospects_by_status', {})}")
                
                print("\n🎉 CORE FUNNEL TEST COMPLETED SUCCESSFULLY!")
                return True
                
            else:
                print("⚠️ No prospects extracted")
                return False
                
        else:
            print("⚠️ No awards found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    try:
        success = await test_simple_funnel()
        if success:
            print("\n✅ Core funnel is working! Ready for production use.")
            print("   Access your dashboard at: http://localhost:5000")
        else:
            print("\n❌ Core funnel test failed.")
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
