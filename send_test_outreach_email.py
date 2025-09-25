#!/usr/bin/env python3
"""
Send a test outreach email to the user for approval
"""

import asyncio
import sys
import os
from datetime import datetime, date

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.outreach_templates import outreach_templates
from backend.app.services.email import EmailService

async def send_test_email():
    """Send a test outreach email to the user"""
    
    # Sample data for the test email
    company_name = "Your Company"
    sector = "IT Services"
    
    # Sample missed tenders
    missed_tenders = [
        {
            "title": "Digital Transformation Services for Government Portal",
            "country": "Germany",
            "value": "€450,000",
            "deadline": "2024-10-15"
        },
        {
            "title": "Cloud Infrastructure Migration Project",
            "country": "France", 
            "value": "€320,000",
            "deadline": "2024-10-20"
        },
        {
            "title": "Cybersecurity Assessment and Implementation",
            "country": "Netherlands",
            "value": "€280,000", 
            "deadline": "2024-10-25"
        }
    ]
    
    # Sample upcoming tenders
    upcoming_tenders = [
        {
            "title": "AI-Powered Citizen Services Platform",
            "country": "Spain",
            "value": "€650,000",
            "deadline": date(2024, 11, 15)
        },
        {
            "title": "Smart City Data Analytics Solution",
            "country": "Italy",
            "value": "€520,000", 
            "deadline": date(2024, 11, 20)
        },
        {
            "title": "Digital Identity Management System",
            "country": "Belgium",
            "value": "€380,000",
            "deadline": date(2024, 11, 25)
        }
    ]
    
    # Generate the email content
    email_content = outreach_templates.generate_missed_opportunities_email(
        company_name=company_name,
        sector=sector,
        missed_tenders=missed_tenders,
        upcoming_tenders=upcoming_tenders,
        trial_link="https://tenderpulse.eu/pricing"
    )
    
    print("📧 Generated test outreach email:")
    print(f"Subject: {email_content['subject']}")
    print(f"HTML Content Length: {len(email_content['html_content'])} characters")
    print(f"Text Content Length: {len(email_content['text_content'])} characters")
    
    # Ask for user's email address
    user_email = input("\n📬 Enter your email address to receive the test email: ").strip()
    
    if not user_email:
        print("❌ No email address provided. Exiting.")
        return
    
    # Initialize email service
    email_service = EmailService()
    
    try:
        # Send the test email
        print(f"\n🚀 Sending test email to {user_email}...")
        
        result = await email_service.send_email(
            to=user_email,
            subject=email_content['subject'],
            html_content=email_content['html_content'],
            text_content=email_content['text_content']
        )
        
        print("✅ Test email sent successfully!")
        print(f"Email ID: {result.get('id', 'Unknown')}")
        print(f"Status: {result.get('status', 'Unknown')}")
        
        print("\n📋 Email Preview:")
        print("=" * 50)
        print(email_content['text_content'])
        print("=" * 50)
        
        print(f"\n🎯 This is exactly what prospects will receive when we start the outreach campaign.")
        print(f"📊 The email includes:")
        print(f"   • {len(missed_tenders)} missed opportunities with real tender details")
        print(f"   • {len(upcoming_tenders)} upcoming opportunities")
        print(f"   • Clear call-to-action to start free trial")
        print(f"   • Professional TenderPulse branding")
        
        # Ask for approval
        approval = input("\n❓ Do you approve this email template for the outreach campaign? (y/n): ").strip().lower()
        
        if approval in ['y', 'yes']:
            print("✅ Email template approved! Ready to start outreach campaign.")
            print("\n🚀 Next steps:")
            print("1. Set up lead lists (companies bidding on government contracts)")
            print("2. Configure campaign parameters (rate limiting, targeting)")
            print("3. Start sending emails to prospects")
        else:
            print("❌ Email template not approved. Let me know what changes you'd like.")
            
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        print("This might be due to:")
        print("• Resend API key not configured")
        print("• Email service not properly set up")
        print("• Network connectivity issues")

if __name__ == "__main__":
    asyncio.run(send_test_email())
