#!/usr/bin/env python3
"""
Enable Automatic Email Sending
Shows how to turn on automatic email sending for your customer acquisition system
"""

import json
import sys
import os

def enable_auto_emails():
    """Enable automatic email sending in the configuration"""
    
    print("🤖 ENABLING AUTOMATIC EMAIL SENDING")
    print("=" * 50)
    
    # Load current config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("📧 Current Email Settings:")
    print(f"   Auto Send: {config['email'].get('auto_send', 'Not set')}")
    print(f"   Send Immediately: {config['email'].get('send_immediately', 'Not set')}")
    print(f"   Batch Size: {config['email'].get('batch_size', 'Not set')}")
    print(f"   Delay Between Emails: {config['email'].get('delay_between_emails', 'Not set')} seconds")
    
    print("\n🔄 Enabling Automatic Email Sending...")
    
    # Enable automatic email sending
    config['email']['auto_send'] = True
    config['email']['send_immediately'] = True
    config['email']['batch_size'] = 5  # Send 5 emails at a time
    config['email']['delay_between_emails'] = 30  # 30 seconds between emails
    
    # Save updated config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Automatic email sending ENABLED!")
    print("\n📧 New Email Settings:")
    print(f"   Auto Send: {config['email']['auto_send']}")
    print(f"   Send Immediately: {config['email']['send_immediately']}")
    print(f"   Batch Size: {config['email']['batch_size']}")
    print(f"   Delay Between Emails: {config['email']['delay_between_emails']} seconds")
    
    print("\n🚀 WHAT HAPPENS NOW:")
    print("   1. ✅ System finds prospects automatically")
    print("   2. ✅ System finds email addresses automatically")
    print("   3. ✅ System generates personalized emails automatically")
    print("   4. 🎯 System SENDS EMAILS AUTOMATICALLY!")
    print("   5. ✅ System tracks responses automatically")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • Emails will be sent to REAL prospects")
    print("   • Make sure SendGrid is verified first")
    print("   • System respects rate limits (100 emails/hour)")
    print("   • 30-second delay between emails to avoid spam filters")
    
    print("\n🛑 TO DISABLE AUTO-SENDING:")
    print("   Run: python3 disable_auto_emails.py")
    
    return True

def disable_auto_emails():
    """Disable automatic email sending"""
    
    print("🛑 DISABLING AUTOMATIC EMAIL SENDING")
    print("=" * 50)
    
    # Load current config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Disable automatic email sending
    config['email']['auto_send'] = False
    config['email']['send_immediately'] = False
    
    # Save updated config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Automatic email sending DISABLED!")
    print("   Emails will now be generated but NOT sent automatically")
    print("   You can still send emails manually from the dashboard")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "disable":
        disable_auto_emails()
    else:
        enable_auto_emails()
