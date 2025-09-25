#!/usr/bin/env python3
"""
View Email Templates and Sequences
Shows you the actual emails that will be sent to prospects
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_ted_prospect_finder import (
    EmailTemplateGenerator, 
    ConfigManager,
    ProspectCompany
)

def create_sample_prospect():
    """Create a sample prospect for email preview"""
    return ProspectCompany(
        company_name="DigitalPartners Ltd",
        country="Germany", 
        sector="IT & Software",
        lost_tender_id="TED-123456",
        lost_tender_title="Germany-Berlin: IT consulting services for digital transformation",
        lost_tender_value="€850,000",
        buyer_name="Berlin Municipality",
        winner_name="CompetitorCorp Ltd",
        lost_date="2024-09-15T00:00:00+02:00",
        pain_level=75,
        contact_name="Michael Schmidt",
        email="m.schmidt@digitalpartners.de",
        status="email_found"
    )

def show_email_templates():
    """Display all email templates and sequences"""
    
    print("📧 TENDERPULSE EMAIL TEMPLATES & SEQUENCES")
    print("=" * 60)
    
    # Initialize email generator
    config = ConfigManager()
    email_generator = EmailTemplateGenerator(config)
    
    # Create sample prospect
    sample_prospect = create_sample_prospect()
    
    print(f"\n🎯 SAMPLE PROSPECT:")
    print(f"   Company: {sample_prospect.company_name}")
    print(f"   Country: {sample_prospect.country}")
    print(f"   Sector: {sample_prospect.sector}")
    print(f"   Lost Tender: {sample_prospect.lost_tender_title}")
    print(f"   Value: {sample_prospect.lost_tender_value}")
    print(f"   Pain Level: {sample_prospect.pain_level}/100")
    
    print("\n" + "="*60)
    print("📧 EMAIL SEQUENCE 1: INITIAL OUTREACH (Day 0)")
    print("="*60)
    
    # Generate initial email
    initial_email = email_generator.generate_personalized_email(sample_prospect)
    
    print(f"\n📨 SUBJECT: {initial_email['subject']}")
    print(f"📊 Personalization Score: {initial_email['prospect_score']}/100")
    print(f"🎯 Personalization Elements:")
    for element in initial_email['personalization_elements']:
        print(f"   • {element}")
    
    print(f"\n📝 EMAIL BODY:")
    print("-" * 40)
    print(initial_email['body'])
    print("-" * 40)
    
    print("\n" + "="*60)
    print("📧 EMAIL SEQUENCE 2: PATTERN RECOGNITION (Day 3)")
    print("="*60)
    
    # Generate follow-up 1
    followup1 = email_generator.generate_followup_email_1(sample_prospect)
    print(f"\n📨 SUBJECT: {followup1['subject']}")
    print(f"\n📝 EMAIL BODY:")
    print("-" * 40)
    print(followup1['body'])
    print("-" * 40)
    
    print("\n" + "="*60)
    print("📧 EMAIL SEQUENCE 3: VALUE-FIRST CLOSE (Day 7)")
    print("="*60)
    
    # Generate follow-up 2
    followup2 = email_generator.generate_followup_email_2(sample_prospect)
    print(f"\n📨 SUBJECT: {followup2['subject']}")
    print(f"\n📝 EMAIL BODY:")
    print("-" * 40)
    print(followup2['body'])
    print("-" * 40)
    
    print("\n" + "="*60)
    print("📊 NEW DATA-DRIVEN EMAIL SEQUENCE SUMMARY")
    print("="*60)
    print("Day 0: Based on TED Award Data - Direct contract reference")
    print("Day 3: Pattern Recognition - Multiple similar contracts")
    print("Day 7: Value-First Close - Final opportunity with clear CTA")
    print("\n🎯 Each email is personalized with:")
    print("   • Specific lost tender details (Berlin, €850K, etc.)")
    print("   • Real contract values and deadlines")
    print("   • Similar buyer patterns (Hamburg, Munich, etc.)")
    print("   • Direct TED links and contract references")
    print("   • Data-driven approach (no generic value props)")
    
    print("\n🚀 WHERE TO VIEW THESE IN THE DASHBOARD:")
    print("   1. Go to: http://localhost:5000")
    print("   2. Login: admin / admin123")
    print("   3. Click 'Emails' in the sidebar")
    print("   4. View 'Email Templates' section")
    print("   5. Click 'Preview' on any template")

def generate_followup_1(prospect):
    """Generate follow-up email 1"""
    return {
        'subject': f"Quick question about {prospect.sector} opportunities in {prospect.country}",
        'body': f"""Hi {prospect.contact_name},

I sent you an email a few days ago about the {prospect.lost_tender_title} contract you recently bid on.

I wanted to follow up because I just found 2 new {prospect.sector} opportunities in {prospect.country} that close next week:

1. {prospect.country} Government: Digital Services Contract
   💰 Value: €{prospect.lost_tender_value}
   ⏰ Deadline: 3 days
   
2. {prospect.buyer_name}: IT Infrastructure Upgrade  
   💰 Value: €650,000
   ⏰ Deadline: 5 days

These are exactly the type of contracts that companies like {prospect.company_name} win with TenderPulse.

Our users typically see 3-5x more relevant opportunities because we monitor ALL procurement portals, not just the obvious ones.

Quick question: Are you currently tracking opportunities across multiple EU procurement systems, or just the main ones?

If you're missing opportunities (which most companies are), I can show you exactly what you're missing in a 5-minute demo.

Just reply "DEMO" and I'll send you a calendar link.

Best,
Alex
TenderPulse

P.S. - The average {prospect.sector} company misses 60% of relevant contracts because they're not monitoring all the right places. Don't let that be you.

---
Reply "STOP" to opt out.
"""
    }

def generate_followup_2(prospect):
    """Generate follow-up email 2"""
    return {
        'subject': f"Last chance: {prospect.sector} opportunities closing this week",
        'body': f"""Hi {prospect.contact_name},

This is my final email about the {prospect.sector} opportunities I found for {prospect.company_name}.

I understand you're busy, but I wanted to make sure you don't miss these:

🔥 URGENT - Closing in 2 days:
• {prospect.country} Digital Transformation Contract
• Value: €{prospect.lost_tender_value}
• Similar to the {prospect.lost_tender_title} you recently bid on

🔥 Closing in 4 days:
• {prospect.buyer_name} IT Services Contract
• Value: €720,000
• Perfect fit for your expertise

Here's the thing - I've been helping {prospect.sector} companies in {prospect.country} win more contracts for 3 years.

The companies that win consistently are the ones that:
✓ See opportunities early (weeks, not days)
✓ Focus on contracts they can actually win
✓ Have templates ready for common requirements

TenderPulse gives you all three.

I'm not going to email you again after this, but if you want to see what opportunities you're missing right now, just reply "YES" and I'll send you a free trial.

No strings attached. Just 5 minutes to see what you're missing.

Best,
Alex
TenderPulse

P.S. - The next big {prospect.sector} contract in {prospect.country} could be published tomorrow. Will you see it?

---
Reply "STOP" to opt out.
"""
    }

if __name__ == "__main__":
    show_email_templates()
