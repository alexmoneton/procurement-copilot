#!/usr/bin/env python3
"""
Simple test email script using direct Resend API
"""

import asyncio
import httpx
import os
from datetime import date

async def send_test_outreach_email():
    """Send a test outreach email using Resend API"""
    
    # Get Resend API key from environment
    resend_api_key = os.getenv('RESEND_API_KEY')
    if not resend_api_key:
        print("❌ RESEND_API_KEY not found in environment variables")
        print("Please set your Resend API key:")
        print("export RESEND_API_KEY=your_resend_api_key_here")
        return
    
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
            "deadline": "November 15, 2024"
        },
        {
            "title": "Smart City Data Analytics Solution",
            "country": "Italy",
            "value": "€520,000", 
            "deadline": "November 20, 2024"
        },
        {
            "title": "Digital Identity Management System",
            "country": "Belgium",
            "value": "€380,000",
            "deadline": "November 25, 2024"
        }
    ]
    
    # Build missed tenders list
    missed_list = ""
    for tender in missed_tenders:
        missed_list += f"• {tender['title']} in {tender['country']} (€{tender['value']})\n"
    
    # Build upcoming tenders list
    upcoming_list = ""
    for tender in upcoming_tenders:
        upcoming_list += f"• {tender['title']} (deadline {tender['deadline']})\n"
    
    # Generate email content
    subject = f"You missed {len(missed_tenders)} tenders in {sector} last month"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{subject}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #f9f9f9; }}
            .header {{ background-color: #003399; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .content {{ padding: 30px; background-color: white; }}
            .tender-list {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .tender-list pre {{ margin: 0; font-family: Arial, sans-serif; white-space: pre-wrap; }}
            .cta {{ text-align: center; margin: 30px 0; }}
            .cta a {{ background-color: #003399; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; }}
            .footer {{ background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            .footer a {{ color: #003399; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 TenderPulse</h1>
                <p>Real-time signals for public contracts</p>
            </div>
            
            <div class="content">
                <h2>Hi {company_name},</h2>
                
                <p>We noticed you've been actively bidding on {sector} tenders, but you might be missing some great opportunities.</p>
                
                <h3>Recent Tenders You Missed:</h3>
                <div class="tender-list">
                    <pre>{missed_list}</pre>
                </div>
                
                <h3>Upcoming Opportunities:</h3>
                <div class="tender-list">
                    <pre>{upcoming_list}</pre>
                </div>
                
                <p>Want alerts and a deadline calendar so you never miss again?</p>
                
                <div class="cta">
                    <a href="https://tenderpulse.eu/pricing">Start Your Free Trial</a>
                </div>
                
                <p>Our AI-powered system monitors 200+ active tenders across Europe and sends personalized alerts directly to your inbox.</p>
                
                <p><strong>What you get:</strong></p>
                <ul>
                    <li>✅ Daily email alerts for relevant tenders</li>
                    <li>✅ Personalized matching based on your business profile</li>
                    <li>✅ Deadline tracking and calendar integration</li>
                    <li>✅ Access to €800M+ in active opportunities</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, <a href="#" class="unsubscribe">unsubscribe here</a>.</p>
                <p>TenderPulse - Real-time signals for public contracts</p>
                <p>Independent service; not affiliated with the EU.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Hi {company_name},
    
    We noticed you've been actively bidding on {sector} tenders, but you might be missing some great opportunities.
    
    Recent Tenders You Missed:
    {missed_list}
    
    Upcoming Opportunities:
    {upcoming_list}
    
    Want alerts and a deadline calendar so you never miss again?
    Start your free trial: https://tenderpulse.eu/pricing
    
    Our AI-powered system monitors 200+ active tenders across Europe and sends personalized alerts directly to your inbox.
    
    What you get:
    ✅ Daily email alerts for relevant tenders
    ✅ Personalized matching based on your business profile  
    ✅ Deadline tracking and calendar integration
    ✅ Access to €800M+ in active opportunities
    
    ---
    This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, unsubscribe here.
    TenderPulse - Real-time signals for public contracts
    Independent service; not affiliated with the EU.
    """
    
    print("📧 Generated test outreach email:")
    print(f"Subject: {subject}")
    print(f"HTML Content Length: {len(html_content)} characters")
    print(f"Text Content Length: {len(html_content)} characters")
    
    # Ask for user's email address
    user_email = input("\n📬 Enter your email address to receive the test email: ").strip()
    
    if not user_email:
        print("❌ No email address provided. Exiting.")
        return
    
    # Send email via Resend API
    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "from": "TenderPulse <alerts@tenderpulse.eu>",
        "to": [user_email],
        "subject": subject,
        "html": html_content,
        "text": text_content,
    }
    
    try:
        print(f"\n🚀 Sending test email to {user_email}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            
            result = response.json()
            print("✅ Test email sent successfully!")
            print(f"Email ID: {result.get('id', 'Unknown')}")
            print(f"Status: {result.get('status', 'Unknown')}")
            
            print("\n📋 Email Preview:")
            print("=" * 50)
            print(text_content)
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
                
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error sending test email: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_outreach_email())
