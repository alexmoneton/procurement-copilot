#!/usr/bin/env python3
"""
Send emails to 5 prospects using the existing system
"""

import sys
import asyncio
import requests
from advanced_ted_prospect_finder import TEDProspectFinder, ConfigManager, ProspectExtractor, EmailTemplateGenerator

async def send_5_prospect_emails():
    """Send emails to 5 prospects"""
    print("🎯 SENDING EMAILS TO 5 PROSPECTS")
    print("="*50)
    
    # Initialize system
    config = ConfigManager()
    finder = TEDProspectFinder(config)
    extractor = ProspectExtractor(config)
    email_generator = EmailTemplateGenerator(config)
    
    # Find recent awards
    print("🔍 Finding recent contract awards...")
    awards = await finder.find_recent_awards()
    print(f"✅ Found {len(awards)} contract awards")
    
    # Extract prospects
    print("👥 Extracting prospects...")
    prospects = extractor.extract_prospects_from_awards(awards)
    print(f"✅ Extracted {len(prospects)} prospects")
    
    # Filter prospects with emails and limit to 5
    prospects_with_emails = []
    for prospect in prospects:
        if prospect.email and len(prospects_with_emails) < 5:
            prospects_with_emails.append(prospect)
    
    print(f"📧 Found {len(prospects_with_emails)} prospects with emails")
    
    if not prospects_with_emails:
        print("❌ No prospects with emails found")
        return 0
    
    # Send emails
    sent_count = 0
    for i, prospect in enumerate(prospects_with_emails, 1):
        print(f"📧 Sending to {i}/5: {prospect.company_name} ({prospect.email})")
        
        try:
            # Generate personalized email content
            email_content = email_generator.generate_personalized_email(prospect)
            
            # Send via Resend API
            response = requests.post(
                'https://api.tenderpulse.eu/api/v1/admin/test-email',
                params={
                    'to': prospect.email,
                    'subject': email_content['subject'],
                    'message': email_content['body']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Sent successfully (ID: {result.get('result', {}).get('id', 'unknown')})")
                sent_count += 1
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Wait between emails (except for the last one)
        if i < len(prospects_with_emails):
            print("   ⏳ Waiting 30 seconds...")
            await asyncio.sleep(30)
    
    print("="*50)
    print(f"📊 EMAIL CAMPAIGN COMPLETE")
    print(f"✅ Successfully sent: {sent_count}/{len(prospects_with_emails)} emails")
    print(f"💰 Revenue potential: {sent_count} prospects contacted")
    
    return sent_count

if __name__ == "__main__":
    result = asyncio.run(send_5_prospect_emails())
    print(f"\n🎉 Campaign result: {result} emails sent successfully!")
