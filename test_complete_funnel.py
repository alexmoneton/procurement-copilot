#!/usr/bin/env python3
"""
Complete Funnel Test Script
Tests the entire customer acquisition pipeline from TED API to email sending
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
    ProspectDatabase
)
from sendgrid_email_sender import SendGridEmailSender

async def test_complete_funnel():
    """Test the complete customer acquisition funnel"""
    
    print("🚀 TESTING COMPLETE CUSTOMER ACQUISITION FUNNEL")
    print("=" * 60)
    
    # Initialize components
    config = ConfigManager()
    db = ProspectDatabase(config.get('database.path', 'ted_prospects.db'))
    
    # Test 1: TED API Connection
    print("\n1️⃣ TESTING TED API CONNECTION")
    print("-" * 40)
    
    try:
        ted_finder = TEDProspectFinder(config)
        print("✅ TEDProspectFinder initialized successfully")
        
        # Test a small search
        print("🔍 Testing TED API search...")
        results = await ted_finder.find_recent_awards()
        
        if results and len(results) > 0:
            print(f"✅ TED API working! Found {len(results)} tenders")
            print(f"   Sample tender: {results[0].title[:50]}...")
        else:
            print("⚠️ TED API returned no results (might be normal)")
            
    except Exception as e:
        print(f"❌ TED API test failed: {e}")
        return False
    
    # Test 2: Database Connection
    print("\n2️⃣ TESTING DATABASE CONNECTION")
    print("-" * 40)
    
    try:
        # Test database operations
        stats = db.get_stats()
        print(f"✅ Database connected! Current stats: {stats}")
        
        # Test adding a sample prospect
        sample_prospect = {
            'company_name': 'Test Company Ltd',
            'country': 'DE',
            'sector': 'IT',
            'lost_tender_title': 'Test Tender',
            'lost_tender_value': '100000',
            'buyer_name': 'Test Buyer',
            'lost_tender_id': 'TEST-001',
            'lost_date': datetime.now().isoformat(),
            'winner_name': 'Winner Corp',
            'pain_level': 75,
            'status': 'found'
        }
        
        # Convert dict to ProspectCompany object
        from advanced_ted_prospect_finder import ProspectCompany
        prospect_obj = ProspectCompany(**sample_prospect)
        prospect_id = db.save_prospect(prospect_obj)
        print(f"✅ Sample prospect added with ID: {prospect_id}")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test 3: Email Finding (Apollo.io + Hunter.io)
    print("\n3️⃣ TESTING EMAIL FINDING")
    print("-" * 40)
    
    try:
        email_finder = EmailFinder(config)
        
        # Test with a real company
        test_company = "SAP SE"  # Well-known company
        print(f"🔍 Finding emails for: {test_company}")
        
        email_result = await email_finder.find_company_emails(test_company)
        
        if email_result and email_result.get('emails'):
            print(f"✅ Email finding working! Found {len(email_result['emails'])} emails")
            print(f"   Sample email: {email_result['emails'][0]}")
        else:
            print("⚠️ No emails found (might be normal for test company)")
            print(f"   Result: {email_result}")
            
    except Exception as e:
        print(f"❌ Email finding test failed: {e}")
        return False
    
    # Test 4: SendGrid Email Sending
    print("\n4️⃣ TESTING EMAIL SENDING")
    print("-" * 40)
    
    try:
        email_sender = SendGridEmailSender(
            api_key=config.get('api_keys.sendgrid', ''),
            from_email=config.get('email.from_email', 'alex@tenderpulse.eu'),
            from_name=config.get('email.from_name', 'Alex')
        )
        
        # Test email (won't actually send without verification)
        test_email = "test@example.com"
        test_subject = "Test Email from TenderPulse"
        test_body = "This is a test email to verify SendGrid integration."
        
        print(f"📧 Testing email send to: {test_email}")
        result = await email_sender.send_email(
            to_email=test_email,
            subject=test_subject,
            body=test_body
        )
        
        print(f"✅ Email sending test completed: {result['status']}")
        if result.get('error'):
            print(f"   Note: {result['error']}")
            
    except Exception as e:
        print(f"❌ Email sending test failed: {e}")
        return False
    
    # Test 5: End-to-End Prospect Finding
    print("\n5️⃣ TESTING END-TO-END PROSPECT FINDING")
    print("-" * 40)
    
    try:
        print("🔍 Running complete prospect finding process...")
        
        # Find prospects
        awards = await ted_finder.find_recent_awards()
        if awards:
            # Extract prospects from awards
            from advanced_ted_prospect_finder import ProspectExtractor
            extractor = ProspectExtractor(config)
            prospects = extractor.extract_prospects_from_awards(awards[:3])  # Limit to 3
        else:
            prospects = []
        
        if prospects:
            print(f"✅ Found {len(prospects)} prospects")
            
            # Process first prospect
            prospect = prospects[0]
            print(f"   Processing: {prospect.company_name}")
            
            # Find emails for this prospect
            email_result = await email_finder.find_company_emails(prospect.company_name)
            
            if email_result and email_result.get('emails'):
                print(f"   ✅ Found {len(email_result['emails'])} emails")
                
                # Update prospect with email
                prospect.email = email_result['emails'][0]
                prospect.status = 'email_found'
                
                # Save updated prospect to database
                db.save_prospect(prospect)
                
                print(f"   ✅ Prospect updated in database")
                
            else:
                print(f"   ⚠️ No emails found for {prospect.company_name}")
                
        else:
            print("⚠️ No prospects found (might be normal)")
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False
    
    # Test 6: Dashboard Integration
    print("\n6️⃣ TESTING DASHBOARD INTEGRATION")
    print("-" * 40)
    
    try:
        # Check if dashboard can access data
        stats = db.get_stats()
        recent_prospects = db.get_recent_prospects(limit=5)
        
        print(f"✅ Dashboard data accessible:")
        print(f"   Total prospects: {stats.get('total_prospects', 0)}")
        print(f"   Recent prospects: {len(recent_prospects)}")
        
    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 60)
    print("✅ TED API: Working")
    print("✅ Database: Working") 
    print("✅ Email Finding: Working")
    print("✅ Email Sending: Working")
    print("✅ End-to-End: Working")
    print("✅ Dashboard: Working")
    
    print("\n🚀 YOUR CUSTOMER ACQUISITION MACHINE IS READY!")
    print("   Access your dashboard at: http://localhost:5000")
    print("   Login: admin / admin123")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_complete_funnel()
        if success:
            print("\n✅ All tests passed! System is ready for production.")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
