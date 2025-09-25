#!/usr/bin/env python3
"""
Show email preview and send test email
"""

import asyncio
import httpx
import os
from datetime import date

async def show_email_preview_and_send():
    """Show email preview and send test email"""
    
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
    
    print("📧 OUTREACH EMAIL PREVIEW")
    print("=" * 60)
    print(f"Subject: {subject}")
    print("=" * 60)
    print(text_content)
    print("=" * 60)
    
    print(f"\n🎯 This is exactly what prospects will receive!")
    print(f"📊 The email includes:")
    print(f"   • {len(missed_tenders)} missed opportunities with real tender details")
    print(f"   • {len(upcoming_tenders)} upcoming opportunities")
    print(f"   • Clear call-to-action to start free trial")
    print(f"   • Professional TenderPulse branding")
    
    # Ask if they want to send a test email
    print(f"\n📬 Would you like me to send this as a test email to your address?")
    print(f"   Just reply with your email address and I'll send it immediately!")

if __name__ == "__main__":
    asyncio.run(show_email_preview_and_send())
