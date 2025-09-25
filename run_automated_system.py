#!/usr/bin/env python3
"""
Run Automated Customer Acquisition System
Finds prospects and sends emails automatically
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
    ProspectExtractor,
    EmailTemplateGenerator
)
# from sendgrid_email_sender import SendGridEmailSender  # Removed - using Resend now

async def run_automated_system():
    """Run the complete automated customer acquisition system"""
    
    print("🤖 AUTOMATED CUSTOMER ACQUISITION SYSTEM")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize components
    config = ConfigManager()
    db = ProspectDatabase(config.get('database.path', 'ted_prospects.db'))
    
    # Check if auto-sending is enabled
    auto_send = config.get('email.auto_send', False)
    print(f"📧 Auto-sending enabled: {auto_send}")
    
    if not auto_send:
        print("⚠️  WARNING: Auto-sending is DISABLED!")
        print("   Run: python3 enable_auto_emails.py")
        print("   Or set 'auto_send': true in config.json")
        print("   Emails will be generated but NOT sent")
    
    print("\n✅ 1. Finding EU Contract Awards")
    print("-" * 40)
    
    try:
        ted_finder = TEDProspectFinder(config)
        awards = await ted_finder.find_recent_awards()
        
        if awards:
            print(f"✅ Found {len(awards)} contract awards from EU")
            
            # Extract prospects
            print("\n✅ 2. Extracting Bid Losers")
            print("-" * 40)
            
            extractor = ProspectExtractor(config)
            prospects = extractor.extract_prospects_from_awards(awards[:10])  # Top 10 for demo
            
            if prospects:
                print(f"✅ Extracted {len(prospects)} prospects")
                
                # Find emails and send
                print("\n✅ 3. Finding Email Addresses & Sending Emails")
                print("-" * 40)
                
                email_finder = EmailFinder(config)
                # Use Resend email system via API
                email_sender = None  # Will use API calls to backend
                email_generator = EmailTemplateGenerator(config)
                
                sent_count = 0
                email_found_count = 0
                
                for i, prospect in enumerate(prospects):
                    print(f"\n📧 Processing {i+1}/{len(prospects)}: {prospect.company_name}")
                    
                    # Find email
                    email_result = await email_finder.find_company_emails(prospect.company_name)
                    
                    if email_result and email_result.get('emails'):
                        # Extract email string from the result
                        email_data = email_result['emails'][0]
                        if isinstance(email_data, dict):
                            prospect.email = email_data.get('value', '')
                        else:
                            prospect.email = str(email_data)
                        
                        if prospect.email:
                            prospect.status = 'email_found'
                            email_found_count += 1
                            print(f"   ✅ Email found: {prospect.email}")
                        else:
                            print(f"   ⚠️  No valid email found")
                            continue
                        
                        # Generate email
                        email_content = email_generator.generate_personalized_email(prospect)
                        
                        # Send email if auto-sending is enabled
                        if auto_send:
                            print(f"   📤 Sending email...")
                            result = await email_sender.send_email(
                                to_email=prospect.email,
                                subject=email_content['subject'],
                                body=email_content['body'],
                                html_body=email_content['html_body']
                            )
                            
                            if result['status'] == 'sent':
                                prospect.status = 'contacted'
                                sent_count += 1
                                print(f"   ✅ Email sent successfully!")
                            else:
                                print(f"   ❌ Email failed: {result.get('error', 'Unknown error')}")
                        else:
                            print(f"   ⚠️  Email generated but NOT sent (auto-sending disabled)")
                            print(f"   📝 Subject: {email_content['subject']}")
                    else:
                        print(f"   ⚠️  No email found")
                    
                    # Save prospect
                    db.save_prospect(prospect)
                    
                    # Rate limiting delay
                    if auto_send and i < len(prospects) - 1:
                        delay = config.get('email.delay_between_emails', 30)
                        print(f"   ⏳ Waiting {delay} seconds before next email...")
                        await asyncio.sleep(delay)
                
                # Final summary
                print("\n" + "=" * 60)
                print("🎉 AUTOMATED SYSTEM COMPLETED!")
                print("=" * 60)
                print(f"📊 Results:")
                print(f"   • Prospects found: {len(prospects)}")
                print(f"   • Emails found: {email_found_count}")
                print(f"   • Emails sent: {sent_count}")
                print(f"   • Success rate: {(sent_count/len(prospects)*100):.1f}%")
                
                if auto_send:
                    print(f"\n🚀 {sent_count} personalized emails sent to real prospects!")
                    print(f"   Check your SendGrid dashboard for delivery status")
                else:
                    print(f"\n⚠️  {email_found_count} emails generated but NOT sent")
                    print(f"   Enable auto-sending to start sending emails")
                
                print(f"\n📱 View results in dashboard: http://localhost:5000")
                
                return True
                
            else:
                print("⚠️ No prospects extracted")
                return False
                
        else:
            print("⚠️ No awards found")
            return False
            
    except Exception as e:
        print(f"❌ System failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    try:
        success = await run_automated_system()
        if success:
            print("\n✅ Automated system completed successfully!")
        else:
            print("\n❌ Automated system failed.")
    except Exception as e:
        print(f"\n💥 System crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
