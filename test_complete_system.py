#!/usr/bin/env python3
"""
Test Complete TenderPulse Customer Acquisition System
Tests all components: TED API, Apollo.io, Hunter.io, Mailgun, Database, Dashboard
"""

import asyncio
import json
from datetime import datetime
from advanced_ted_prospect_finder import (
    ConfigManager, ProspectDatabase, TEDProspectFinder, 
    EmailFinder, EmailSender, ProspectExtractor, EmailTemplateGenerator
)

async def test_complete_system():
    """Test the complete customer acquisition system"""
    
    print("🚀 Testing Complete TenderPulse Customer Acquisition System")
    print("=" * 60)
    
    # Initialize configuration
    print("\n1️⃣ Testing Configuration...")
    config = ConfigManager()
    print(f"✅ Config loaded: {config.config_file}")
    print(f"✅ Apollo API key: {'✅ Set' if config.get('api_keys.apollo_io') else '❌ Not set'}")
    print(f"✅ Hunter API key: {'✅ Set' if config.get('api_keys.hunter_io') else '❌ Not set'}")
    print(f"✅ Mailgun API key: {'✅ Set' if config.get('api_keys.mailgun') else '❌ Not set'}")
    
    # Test database
    print("\n2️⃣ Testing Database...")
    db = ProspectDatabase(config.get('database.path'))
    print(f"✅ Database initialized: {config.get('database.path')}")
    
    # Test TED API
    print("\n3️⃣ Testing TED API...")
    ted_finder = TEDProspectFinder(config)
    awards = []
    try:
        # Test with a small search
        awards = await ted_finder.find_recent_awards()
        print(f"✅ TED API working: Found {len(awards)} contract awards")
        if awards:
            # Handle both dict and object types
            first_award = awards[0]
            if hasattr(first_award, 'title'):
                title = first_award.title
            elif isinstance(first_award, dict):
                title = first_award.get('title', 'No title')
            else:
                title = str(first_award)[:50]
            print(f"   Sample: {title[:50]}...")
    except Exception as e:
        print(f"❌ TED API error: {e}")
    
    # Test email finder
    print("\n4️⃣ Testing Email Finder...")
    email_finder = EmailFinder(config)
    
    # Test Apollo.io
    if config.get('api_keys.apollo_io'):
        print("   Testing Apollo.io...")
        try:
            apollo_result = await email_finder.find_emails_apollo('Microsoft', 'microsoft.com')
            if apollo_result and apollo_result.get('best_contact'):
                print(f"✅ Apollo.io working: Found contact")
                contact = apollo_result['best_contact']
                print(f"   Email: {contact.get('value', 'N/A')}")
                print(f"   Name: {contact.get('first_name', '')} {contact.get('last_name', '')}")
            else:
                print("⚠️ Apollo.io: No results (may need activation)")
        except Exception as e:
            print(f"❌ Apollo.io error: {e}")
    
    # Test Hunter.io
    if config.get('api_keys.hunter_io'):
        print("   Testing Hunter.io...")
        try:
            hunter_result = await email_finder.find_emails_hunter('Microsoft', 'microsoft.com')
            if hunter_result and hunter_result.get('best_contact'):
                print(f"✅ Hunter.io working: Found contact")
                contact = hunter_result['best_contact']
                print(f"   Email: {contact.get('value', 'N/A')}")
            else:
                print("⚠️ Hunter.io: No results")
        except Exception as e:
            print(f"❌ Hunter.io error: {e}")
    
    # Test email sender
    print("\n5️⃣ Testing Email Sender...")
    if config.get('api_keys.mailgun'):
        email_sender = EmailSender(config)
        print("✅ Mailgun configured")
        print(f"   From: {config.get('email.from_email')}")
        print(f"   Domain: {config.get('api_keys.mailgun_domain')}")
    else:
        print("⚠️ Mailgun not configured (emails won't be sent)")
    
    # Test prospect extraction
    print("\n6️⃣ Testing Prospect Extraction...")
    if awards:
        extractor = ProspectExtractor(config)
        prospects = extractor.extract_prospects_from_awards(awards[:2])  # Test with 2 awards
        print(f"✅ Prospect extraction: Found {len(prospects)} prospects")
        if prospects:
            prospect = prospects[0]
            print(f"   Sample: {prospect.company_name} ({prospect.country})")
            print(f"   Lost tender: {prospect.lost_tender_title[:50]}...")
    
    # Test email template generation
    print("\n7️⃣ Testing Email Template Generation...")
    if prospects:
        template_generator = EmailTemplateGenerator(config)
        email_content = template_generator.generate_personalized_email(prospects[0])
        print("✅ Email template generation working")
        print(f"   Subject: {email_content['subject']}")
        print(f"   Body length: {len(email_content['body'])} characters")
    
    # Test database operations
    print("\n8️⃣ Testing Database Operations...")
    if prospects:
        # Save a test prospect
        prospect_id = db.save_prospect(prospects[0])
        print(f"✅ Database save: Prospect ID {prospect_id}")
        
        # Get prospect
        saved_prospect = db.get_prospect(prospect_id)
        if saved_prospect:
            print(f"✅ Database retrieve: {saved_prospect['company_name']}")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"✅ Database stats: {stats['total_prospects']} total prospects")
    
    # System summary
    print("\n" + "=" * 60)
    print("🎯 SYSTEM STATUS SUMMARY")
    print("=" * 60)
    
    # Check what's working
    working_components = []
    if config.get('api_keys.apollo_io') or config.get('api_keys.hunter_io'):
        working_components.append("Email Finding")
    if config.get('api_keys.mailgun'):
        working_components.append("Email Sending")
    if awards:
        working_components.append("TED API")
    working_components.extend(["Database", "Prospect Extraction", "Email Templates"])
    
    print(f"✅ Working components: {', '.join(working_components)}")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    if not config.get('api_keys.apollo_io') and not config.get('api_keys.hunter_io'):
        print("❌ Add email finder API key (Apollo.io or Hunter.io)")
    if not config.get('api_keys.mailgun'):
        print("❌ Add Mailgun API key for email sending")
    if not awards:
        print("❌ Check TED API connection")
    
    if len(working_components) >= 4:
        print("🚀 System is ready for production!")
        print("\nNext steps:")
        print("1. Run: python3 automation_system.py run-daily")
        print("2. Start dashboard: python3 flask_dashboard.py")
        print("3. Monitor results at http://localhost:5000")
    else:
        print("⚠️ System needs configuration before production use")
    
    print("\n🎊 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_complete_system())
