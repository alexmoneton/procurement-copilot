#!/usr/bin/env python3
"""
Unified Email System for TenderPulse
Centralized email sending with vendor abstraction, suppression management, and compliance features.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Header, CustomArg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProvider(Enum):
    SENDGRID = "sendgrid"
    RESEND = "resend"
    MAILGUN = "mailgun"

@dataclass
class EmailResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None

@dataclass
class SuppressionEntry:
    email: str
    reason: str  # 'bounce', 'complaint', 'unsubscribe', 'manual'
    timestamp: datetime
    source: str  # 'webhook', 'manual', 'api'

class UnifiedMailer:
    """
    Unified email system with vendor abstraction, suppression management, and compliance features.
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.provider = EmailProvider(self.config.get('email_provider', 'sendgrid'))
        self.suppression_table = {}  # In production, use Redis or database
        self.tracking_domains = self.config.get('tracking_domains', {})
        
        # Initialize provider
        if self.provider == EmailProvider.SENDGRID:
            self._init_sendgrid()
        elif self.provider == EmailProvider.RESEND:
            self._init_resend()
        elif self.provider == EmailProvider.MAILGUN:
            self._init_mailgun()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            return {}
    
    def _init_sendgrid(self):
        """Initialize SendGrid client."""
        api_key = self.config.get('sendgrid', {}).get('api_key')
        if not api_key:
            raise ValueError("SendGrid API key not found in config")
        
        self.client = SendGridAPIClient(api_key=api_key)
        self.from_email = self.config.get('sendgrid', {}).get('from_email', 'alex@tenderpulse.eu')
        self.from_name = self.config.get('sendgrid', {}).get('from_name', 'TenderPulse')
        
        logger.info("SendGrid client initialized")
    
    def _init_resend(self):
        """Initialize Resend client."""
        api_key = self.config.get('resend', {}).get('api_key')
        if not api_key:
            raise ValueError("Resend API key not found in config")
        
        self.client = requests.Session()
        self.client.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        self.from_email = self.config.get('resend', {}).get('from_email', 'alex@tenderpulse.eu')
        self.from_name = self.config.get('resend', {}).get('from_name', 'TenderPulse')
        
        logger.info("Resend client initialized")
    
    def _init_mailgun(self):
        """Initialize Mailgun client."""
        api_key = self.config.get('mailgun', {}).get('api_key')
        domain = self.config.get('mailgun', {}).get('domain')
        if not api_key or not domain:
            raise ValueError("Mailgun API key or domain not found in config")
        
        self.client = requests.Session()
        self.client.auth = ('api', api_key)
        self.domain = domain
        self.from_email = self.config.get('mailgun', {}).get('from_email', 'alex@tenderpulse.eu')
        self.from_name = self.config.get('mailgun', {}).get('from_name', 'TenderPulse')
        
        logger.info("Mailgun client initialized")
    
    def is_suppressed(self, email: str) -> bool:
        """Check if email is in suppression table."""
        return email.lower() in self.suppression_table
    
    def add_suppression(self, email: str, reason: str, source: str = 'manual'):
        """Add email to suppression table."""
        self.suppression_table[email.lower()] = SuppressionEntry(
            email=email.lower(),
            reason=reason,
            timestamp=datetime.now(),
            source=source
        )
        logger.info(f"Added {email} to suppression table: {reason}")
    
    def remove_suppression(self, email: str) -> bool:
        """Remove email from suppression table."""
        if email.lower() in self.suppression_table:
            del self.suppression_table[email.lower()]
            logger.info(f"Removed {email} from suppression table")
            return True
        return False
    
    def get_tracking_domain(self, campaign: str) -> str:
        """Get custom tracking domain for campaign."""
        return self.tracking_domains.get(campaign, self.config.get('default_tracking_domain', 'tenderpulse.eu'))
    
    def _generate_unsubscribe_url(self, email: str, campaign: str) -> str:
        """Generate unsubscribe URL with tracking."""
        tracking_domain = self.get_tracking_domain(campaign)
        token = self._generate_unsubscribe_token(email, campaign)
        return f"https://{tracking_domain}/unsubscribe?token={token}&email={email}"
    
    def _generate_unsubscribe_token(self, email: str, campaign: str) -> str:
        """Generate secure unsubscribe token."""
        secret = self.config.get('unsubscribe_secret', 'default_secret')
        data = f"{email}:{campaign}:{secret}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        campaign: str = 'default',
        tags: List[str] = None,
        custom_args: Dict[str, str] = None,
        reply_to: str = None
    ) -> EmailResult:
        """
        Send email through configured provider with compliance features.
        """
        # Check suppression
        if self.is_suppressed(to_email):
            logger.warning(f"Email {to_email} is suppressed, skipping send")
            return EmailResult(success=False, error="Email is suppressed")
        
        # Generate unsubscribe URL
        unsubscribe_url = self._generate_unsubscribe_url(to_email, campaign)
        
        # Add compliance headers
        headers = {
            'List-Unsubscribe': f'<{unsubscribe_url}>, <mailto:unsubscribe@tenderpulse.eu>',
            'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
            'X-Campaign': campaign,
            'X-Mailer': 'TenderPulse-Mailer-v1.0'
        }
        
        # Add custom tracking domain
        tracking_domain = self.get_tracking_domain(campaign)
        if tracking_domain != 'tenderpulse.eu':
            headers['X-Tracking-Domain'] = tracking_domain
        
        # Send via configured provider
        if self.provider == EmailProvider.SENDGRID:
            return self._send_via_sendgrid(
                to_email, subject, html_content, text_content, 
                headers, tags, custom_args, reply_to
            )
        elif self.provider == EmailProvider.RESEND:
            return self._send_via_resend(
                to_email, subject, html_content, text_content, 
                headers, tags, custom_args, reply_to
            )
        elif self.provider == EmailProvider.MAILGUN:
            return self._send_via_mailgun(
                to_email, subject, html_content, text_content, 
                headers, tags, custom_args, reply_to
            )
    
    def _send_via_sendgrid(
        self, to_email: str, subject: str, html_content: str, text_content: str,
        headers: Dict, tags: List[str], custom_args: Dict, reply_to: str
    ) -> EmailResult:
        """Send email via SendGrid."""
        try:
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            # Create content
            content = Content("text/html", html_content)
            if text_content:
                content = Content("text/plain", text_content)
            
            # Create mail object
            mail = Mail(from_email, to_email_obj, subject, content)
            
            # Add headers
            for key, value in headers.items():
                mail.add_header(Header(key, value))
            
            # Add custom args
            if custom_args:
                for key, value in custom_args.items():
                    mail.add_custom_arg(CustomArg(key, value))
            
            # Add tags
            if tags:
                for tag in tags:
                    mail.add_category(tag)
            
            # Set reply-to
            if reply_to:
                mail.reply_to = Email(reply_to)
            
            # Send
            response = self.client.send(mail)
            
            if response.status_code in [200, 201, 202]:
                return EmailResult(
                    success=True,
                    message_id=response.headers.get('X-Message-Id'),
                    provider='sendgrid'
                )
            else:
                return EmailResult(
                    success=False,
                    error=f"SendGrid error: {response.status_code} - {response.body}",
                    provider='sendgrid'
                )
                
        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return EmailResult(success=False, error=str(e), provider='sendgrid')
    
    def _send_via_resend(
        self, to_email: str, subject: str, html_content: str, text_content: str,
        headers: Dict, tags: List[str], custom_args: Dict, reply_to: str
    ) -> EmailResult:
        """Send email via Resend."""
        try:
            data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': [to_email],
                'subject': subject,
                'html': html_content,
                'headers': headers
            }
            
            if text_content:
                data['text'] = text_content
            
            if tags:
                data['tags'] = [{'name': tag} for tag in tags]
            
            if custom_args:
                data['tags'].extend([{'name': f"{k}:{v}"} for k, v in custom_args.items()])
            
            if reply_to:
                data['reply_to'] = reply_to
            
            response = self.client.post('https://api.resend.com/emails', json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return EmailResult(
                    success=True,
                    message_id=result.get('id'),
                    provider='resend'
                )
            else:
                return EmailResult(
                    success=False,
                    error=f"Resend error: {response.status_code} - {response.text}",
                    provider='resend'
                )
                
        except Exception as e:
            logger.error(f"Resend send error: {e}")
            return EmailResult(success=False, error=str(e), provider='resend')
    
    def _send_via_mailgun(
        self, to_email: str, subject: str, html_content: str, text_content: str,
        headers: Dict, tags: List[str], custom_args: Dict, reply_to: str
    ) -> EmailResult:
        """Send email via Mailgun."""
        try:
            data = {
                'from': f"{self.from_name} <{self.from_email}>",
                'to': to_email,
                'subject': subject,
                'html': html_content
            }
            
            if text_content:
                data['text'] = text_content
            
            if tags:
                data['o:tag'] = tags
            
            if custom_args:
                for key, value in custom_args.items():
                    data[f'v:{key}'] = value
            
            if reply_to:
                data['h:Reply-To'] = reply_to
            
            # Add headers
            for key, value in headers.items():
                data[f'h:{key}'] = value
            
            response = self.client.post(
                f'https://api.mailgun.net/v3/{self.domain}/messages',
                data=data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return EmailResult(
                    success=True,
                    message_id=result.get('id'),
                    provider='mailgun'
                )
            else:
                return EmailResult(
                    success=False,
                    error=f"Mailgun error: {response.status_code} - {response.text}",
                    provider='mailgun'
                )
                
        except Exception as e:
            logger.error(f"Mailgun send error: {e}")
            return EmailResult(success=False, error=str(e), provider='mailgun')
    
    def get_suppression_stats(self) -> Dict:
        """Get suppression table statistics."""
        stats = {
            'total_suppressed': len(self.suppression_table),
            'by_reason': {},
            'by_source': {},
            'recent_suppressions': []
        }
        
        for entry in self.suppression_table.values():
            # Count by reason
            stats['by_reason'][entry.reason] = stats['by_reason'].get(entry.reason, 0) + 1
            
            # Count by source
            stats['by_source'][entry.source] = stats['by_source'].get(entry.source, 0) + 1
            
            # Recent suppressions (last 24h)
            if entry.timestamp > datetime.now() - timedelta(days=1):
                stats['recent_suppressions'].append({
                    'email': entry.email,
                    'reason': entry.reason,
                    'timestamp': entry.timestamp.isoformat()
                })
        
        return stats

# Global mailer instance
_mailer_instance = None

def get_mailer() -> UnifiedMailer:
    """Get global mailer instance."""
    global _mailer_instance
    if _mailer_instance is None:
        _mailer_instance = UnifiedMailer()
    return _mailer_instance

def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None,
    campaign: str = 'default',
    tags: List[str] = None,
    custom_args: Dict[str, str] = None
) -> EmailResult:
    """Convenience function for sending emails."""
    mailer = get_mailer()
    return mailer.send_email(
        to_email, subject, html_content, text_content,
        campaign, tags, custom_args
    )

if __name__ == "__main__":
    # Test the mailer
    mailer = UnifiedMailer()
    
    # Test suppression
    mailer.add_suppression("test@example.com", "bounce", "webhook")
    print(f"Is suppressed: {mailer.is_suppressed('test@example.com')}")
    
    # Test stats
    stats = mailer.get_suppression_stats()
    print(f"Suppression stats: {stats}")
    
    print("✅ Unified mailer initialized successfully!")
