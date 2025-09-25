#!/usr/bin/env python3
"""
SendGrid Email Sender for TenderPulse
Replaces Mailgun with SendGrid for better deliverability and features
"""

import asyncio
import logging
from typing import Dict, List, Optional
from email_validator import validate_email, EmailNotValidError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger('sendgrid_sender')

class SendGridEmailSender:
    """SendGrid integration for sending emails"""
    
    def __init__(self, api_key: str, from_email: str, from_name: str = None):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name or from_email.split('@')[0]
        self.sg = SendGridAPIClient(api_key) if api_key else None
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        html_body: str = None, tags: List[str] = None) -> Dict:
        """Send email via SendGrid"""
        if not self.sg:
            logger.warning("⚠️ SendGrid not configured - would send email")
            return {
                'status': 'not_sent',
                'reason': 'SendGrid not configured',
                'to': to_email,
                'subject': subject
            }
        
        # Validate email
        try:
            validated_email = validate_email(to_email)
            to_email = validated_email.email
        except EmailNotValidError:
            logger.warning(f"Invalid email address: {to_email}")
            return {'status': 'invalid_email'}
        
        try:
            # Create SendGrid message
            from_email_obj = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            # Use HTML content if provided, otherwise plain text
            content = Content("text/html", html_body) if html_body else Content("text/plain", body)
            
            message = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=body,
                html_content=html_body
            )
            
            # Add tags if provided
            if tags:
                for tag in tags:
                    message.add_category(tag)
            
            # Send email
            response = self.sg.send(message)
            
            # Debug response
            print(f"Response type: {type(response)}")
            print(f"Response: {response}")
            
            if hasattr(response, 'status_code') and response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email} via SendGrid")
                return {
                    'status': 'sent',
                    'id': str(getattr(response, 'headers', {}).get('X-Message-Id', '')),
                    'to': to_email,
                    'subject': subject,
                    'status_code': response.status_code
                }
            else:
                logger.error(f"❌ SendGrid error: {getattr(response, 'status_code', 'unknown')}")
                return {
                    'status': 'failed',
                    'error': f"HTTP {getattr(response, 'status_code', 'unknown')}",
                    'to': to_email,
                    'subject': subject
                }
                
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'to': to_email,
                'subject': subject
            }
    
    def send_email_sync(self, to_email: str, subject: str, body: str, 
                       html_body: str = None, tags: List[str] = None) -> Dict:
        """Synchronous version of send_email"""
        return asyncio.run(self.send_email(to_email, subject, body, html_body, tags))

# Test function
async def test_sendgrid():
    """Test SendGrid integration"""
    api_key = "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"
    sender = SendGridEmailSender(
        api_key=api_key,
        from_email="hello@tenderpulse.eu",
        from_name="Alex from TenderPulse"
    )
    
    result = await sender.send_email(
        to_email="test@example.com",
        subject="Test Email from TenderPulse",
        body="This is a test email from TenderPulse customer acquisition system.",
        html_body="<h1>Test Email</h1><p>This is a test email from <strong>TenderPulse</strong> customer acquisition system.</p>",
        tags=["test", "tenderpulse"]
    )
    
    print(f"SendGrid test result: {result}")
    return result

if __name__ == "__main__":
    asyncio.run(test_sendgrid())
