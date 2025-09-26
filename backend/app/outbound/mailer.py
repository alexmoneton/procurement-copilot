"""
Resend mailer system for sending outbound emails.
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..db.models_outbound import Prospect, OutboundLog, OutboundEvent, Suppression
from ..core.config import settings
from .utils import (
    sign_unsub, is_role_email, is_domain_blacklisted, 
    format_currency, truncate_text, validate_email_format
)

logger = logging.getLogger(__name__)


class ResendMailer:
    """Resend mailer system for outbound emails."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.api_key = settings.resend_api_key
        self.base_url = "https://api.resend.com"
        self.from_email = settings.email_from
        self.from_name = settings.email_from_name
        self.unsub_base_url = settings.list_unsub_base_url
        self.daily_cap = settings.outbound_max_emails_per_day
        self._daily_sent = 0
        self._last_reset_date = datetime.utcnow().date()
    
    async def send_outbound(
        self, 
        prospect: Prospect, 
        email: str, 
        template_id: str = "missed_opportunities_v1"
    ) -> bool:
        """
        Send outbound email to prospect.
        
        Args:
            prospect: Prospect to send email to
            email: Email address
            template_id: Email template ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Check daily cap
            if not await self._check_daily_cap():
                self.logger.warning("Daily email cap reached")
                return False
            
            # Check suppression list
            if await self._is_suppressed(email):
                self.logger.info(f"Email {email} is suppressed")
                return False
            
            # Check if role email
            if is_role_email(email):
                self.logger.info(f"Email {email} is a role email, skipping")
                return False
            
            # Generate email content
            email_content = await self._generate_email_content(prospect, email, template_id)
            if not email_content:
                return False
            
            # Send email
            success = await self._send_email(email, email_content)
            
            if success:
                # Update prospect status
                prospect.status = "sent"
                
                # Log email sent
                log_entry = OutboundLog(
                    prospect_id=prospect.id,
                    email=email,
                    campaign=template_id,
                    event=OutboundEvent.SENT,
                    meta={"template": template_id, "sent_at": datetime.utcnow().isoformat()}
                )
                self.db.add(log_entry)
                
                self._daily_sent += 1
                await self.db.commit()
                
                self.logger.info(f"Sent email to {email} for prospect {prospect.id}")
                return True
            else:
                # Log error
                log_entry = OutboundLog(
                    prospect_id=prospect.id,
                    email=email,
                    campaign=template_id,
                    event=OutboundEvent.ERROR,
                    meta={"error": "Failed to send email"}
                )
                self.db.add(log_entry)
                await self.db.commit()
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending email to {email}: {e}")
            return False
    
    async def _check_daily_cap(self) -> bool:
        """
        Check if daily email cap is reached.
        
        Returns:
            True if under cap, False if cap reached
        """
        try:
            # Reset daily usage if new day
            current_date = datetime.utcnow().date()
            if current_date > self._last_reset_date:
                self._daily_sent = 0
                self._last_reset_date = current_date
            
            # Check against cap
            if self._daily_sent >= self.daily_cap:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking daily cap: {e}")
            return False
    
    async def _is_suppressed(self, email: str) -> bool:
        """
        Check if email is in suppression list.
        
        Args:
            email: Email to check
            
        Returns:
            True if suppressed, False otherwise
        """
        try:
            query = select(Suppression).where(Suppression.email == email)
            result = await self.db.execute(query)
            suppressed = result.scalar_one_or_none()
            
            return suppressed is not None
            
        except Exception as e:
            self.logger.error(f"Error checking suppression: {e}")
            return False
    
    async def _generate_email_content(
        self, 
        prospect: Prospect, 
        email: str, 
        template_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate email content for prospect.
        
        Args:
            prospect: Prospect
            email: Email address
            template_id: Template ID
            
        Returns:
            Email content dictionary or None
        """
        try:
            # Generate unsubscribe token
            unsubscribe_token = sign_unsub(email, settings.secret_key)
            unsubscribe_url = f"{self.unsub_base_url}?e={base64.urlsafe_b64encode(email.encode()).decode()}&t={unsubscribe_token}"
            
            # Get similar tenders (mock data for now)
            similar_tenders = await self._get_similar_tenders(prospect)
            
            # Generate subject
            subject = f"Similar €{format_currency(prospect.score * 1000000, 'EUR')} contract to your {prospect.country.upper()} bid"
            
            # Generate HTML content
            html_content = self._generate_html_content(
                prospect, 
                similar_tenders, 
                unsubscribe_url
            )
            
            # Generate text content
            text_content = self._generate_text_content(
                prospect, 
                similar_tenders, 
                unsubscribe_url
            )
            
            return {
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "unsubscribe_url": unsubscribe_url
            }
            
        except Exception as e:
            self.logger.error(f"Error generating email content: {e}")
            return None
    
    async def _get_similar_tenders(self, prospect: Prospect) -> List[Dict[str, Any]]:
        """
        Get similar tenders for prospect.
        
        Args:
            prospect: Prospect
            
        Returns:
            List of similar tender dictionaries
        """
        # Mock data for now - in practice you'd query the database
        return [
            {
                "title": f"IT Services Contract - {prospect.country.upper()}",
                "value": 500000,
                "currency": "EUR",
                "deadline": "2024-02-15",
                "buyer": "Government Agency",
                "url": "https://ted.europa.eu/en/notice/-/detail/123456"
            },
            {
                "title": f"Consulting Services - {prospect.country.upper()}",
                "value": 750000,
                "currency": "EUR",
                "deadline": "2024-02-20",
                "buyer": "Public Authority",
                "url": "https://ted.europa.eu/en/notice/-/detail/123457"
            }
        ]
    
    def _generate_html_content(
        self, 
        prospect: Prospect, 
        similar_tenders: List[Dict], 
        unsubscribe_url: str
    ) -> str:
        """
        Generate HTML email content.
        
        Args:
            prospect: Prospect
            similar_tenders: List of similar tenders
            unsubscribe_url: Unsubscribe URL
            
        Returns:
            HTML content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Similar Tender Opportunities</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Similar Tender Opportunities</h2>
                
                <p>Hi there,</p>
                
                <p>I noticed you recently bid on a tender in {prospect.country.upper()}. I found some similar opportunities that might interest you:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Current Opportunities</h3>
        """
        
        for tender in similar_tenders:
            html += f"""
                    <div style="border-bottom: 1px solid #dee2e6; padding: 15px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #495057;">{tender['title']}</h4>
                        <p style="margin: 5px 0;"><strong>Value:</strong> {format_currency(tender['value'], tender['currency'])}</p>
                        <p style="margin: 5px 0;"><strong>Buyer:</strong> {tender['buyer']}</p>
                        <p style="margin: 5px 0;"><strong>Deadline:</strong> {tender['deadline']}</p>
                        <p style="margin: 10px 0;"><a href="{tender['url']}" style="color: #007bff; text-decoration: none;">View Tender Details →</a></p>
                    </div>
            """
        
        html += f"""
                </div>
                
                <p>If you'd like to get notified about similar opportunities automatically, you can try TenderPulse for free:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://tenderpulse.eu/trial" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Start Free Trial</a>
                </div>
                
                <p>Best regards,<br>Alexandre Monéton<br>TenderPulse</p>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #6c757d;">
                    You received this email because you recently participated in EU public procurement.<br>
                    <a href="{unsubscribe_url}" style="color: #6c757d;">Unsubscribe</a> | 
                    <a href="https://tenderpulse.eu/privacy" style="color: #6c757d;">Privacy Policy</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_content(
        self, 
        prospect: Prospect, 
        similar_tenders: List[Dict], 
        unsubscribe_url: str
    ) -> str:
        """
        Generate text email content.
        
        Args:
            prospect: Prospect
            similar_tenders: List of similar tenders
            unsubscribe_url: Unsubscribe URL
            
        Returns:
            Text content
        """
        text = f"""Similar Tender Opportunities

Hi there,

I noticed you recently bid on a tender in {prospect.country.upper()}. I found some similar opportunities that might interest you:

Current Opportunities:
"""
        
        for tender in similar_tenders:
            text += f"""
{tender['title']}
Value: {format_currency(tender['value'], tender['currency'])}
Buyer: {tender['buyer']}
Deadline: {tender['deadline']}
View: {tender['url']}
"""
        
        text += f"""
If you'd like to get notified about similar opportunities automatically, you can try TenderPulse for free:
https://tenderpulse.eu/trial

Best regards,
Alexandre Monéton
TenderPulse

---
You received this email because you recently participated in EU public procurement.
Unsubscribe: {unsubscribe_url}
Privacy Policy: https://tenderpulse.eu/privacy
"""
        
        return text
    
    async def _send_email(self, email: str, content: Dict[str, Any]) -> bool:
        """
        Send email via Resend API.
        
        Args:
            email: Recipient email
            content: Email content
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [email],
                "subject": content["subject"],
                "html": content["html"],
                "text": content["text"],
                "headers": {
                    "List-Unsubscribe": f"<{content['unsubscribe_url']}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Email sent successfully to {email}")
                    return True
                else:
                    self.logger.error(f"Failed to send email to {email}: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending email to {email}: {e}")
            return False
    
    async def send_batch(
        self, 
        prospects: List[Prospect], 
        max_sends: int = 100
    ) -> Dict[str, int]:
        """
        Send emails to multiple prospects.
        
        Args:
            prospects: List of prospects
            max_sends: Maximum number of emails to send
            
        Returns:
            Dictionary with sending statistics
        """
        sent_count = 0
        error_count = 0
        
        try:
            for prospect in prospects:
                if sent_count >= max_sends:
                    break
                
                if prospect.status != "enriched":
                    continue
                
                # Get email from cache or prospect
                email = await self._get_prospect_email(prospect)
                if not email:
                    continue
                
                success = await self.send_outbound(prospect, email)
                if success:
                    sent_count += 1
                else:
                    error_count += 1
                
                # Rate limiting
                await asyncio.sleep(2)  # 2 seconds between sends
            
            return {
                "prospects_processed": len(prospects),
                "emails_sent": sent_count,
                "errors": error_count,
                "daily_sent": self._daily_sent
            }
            
        except Exception as e:
            self.logger.error(f"Error in batch sending: {e}")
            return {
                "prospects_processed": len(prospects),
                "emails_sent": 0,
                "errors": len(prospects),
                "error": str(e)
            }
    
    async def _get_prospect_email(self, prospect: Prospect) -> Optional[str]:
        """
        Get email for prospect.
        
        Args:
            prospect: Prospect
            
        Returns:
            Email address or None
        """
        try:
            # Query for recent outbound log with email
            query = select(OutboundLog).where(
                and_(
                    OutboundLog.prospect_id == prospect.id,
                    OutboundLog.event == OutboundEvent.QUEUED
                )
            ).order_by(OutboundLog.created_at.desc())
            
            result = await self.db.execute(query)
            log_entry = result.scalar_one_or_none()
            
            if log_entry:
                return log_entry.email
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting prospect email: {e}")
            return None
