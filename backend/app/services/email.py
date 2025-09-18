"""Email service for sending notifications."""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from loguru import logger

from ..core.config import settings


class EmailProvider:
    """Base email provider interface."""
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> Dict[str, Any]:
        """Send an email."""
        raise NotImplementedError


class ResendEmailProvider(EmailProvider):
    """Resend email provider implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.resend.com"
        self.logger = logger.bind(service="resend_email")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> Dict[str, Any]:
        """Send email via Resend API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "from": "Procurement Copilot <noreply@procurement-copilot.com>",
            "to": [to],
            "subject": subject,
            "html": html_content,
            "text": text_content,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                result = response.json()
                self.logger.info(f"Email sent successfully to {to}: {result.get('id')}")
                return result
                
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Resend API error: {e.response.status_code} - {e.response.text}")
            raise EmailError(f"Failed to send email: {e.response.status_code}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {e}")
            raise EmailError(f"Failed to send email: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise EmailError(f"Failed to send email: {e}")


class MockEmailProvider(EmailProvider):
    """Mock email provider for testing."""
    
    def __init__(self):
        self.sent_emails = []
        self.logger = logger.bind(service="mock_email")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> Dict[str, Any]:
        """Mock email sending."""
        email_data = {
            "to": to,
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content,
            "sent_at": datetime.now(),
        }
        
        self.sent_emails.append(email_data)
        self.logger.info(f"Mock email sent to {to}: {subject}")
        
        return {
            "id": f"mock-{len(self.sent_emails)}",
            "to": to,
            "subject": subject,
        }


class EmailError(Exception):
    """Email service error."""
    pass


class EmailService:
    """Email service for sending tender notifications."""
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        self.provider = provider or self._create_provider()
        self.logger = logger.bind(service="email_service")
    
    def _create_provider(self) -> EmailProvider:
        """Create email provider based on configuration."""
        api_key = getattr(settings, 'resend_api_key', None)
        
        if not api_key:
            self.logger.warning("No Resend API key configured, using mock provider")
            return MockEmailProvider()
        
        return ResendEmailProvider(api_key)
    
    def _format_currency(self, amount: Optional[Decimal], currency: Optional[str]) -> str:
        """Format currency amount for display."""
        if not amount:
            return "N/A"
        
        if currency:
            return f"{amount:,.2f} {currency}"
        else:
            return f"{amount:,.2f}"
    
    def _format_cpv_codes(self, cpv_codes: List[str], max_codes: int = 3) -> str:
        """Format CPV codes for display."""
        if not cpv_codes:
            return "N/A"
        
        # Take first max_codes codes
        display_codes = cpv_codes[:max_codes]
        formatted = ", ".join(display_codes)
        
        if len(cpv_codes) > max_codes:
            formatted += f" (+{len(cpv_codes) - max_codes} more)"
        
        return formatted
    
    def _format_deadline(self, deadline_date: Optional[datetime]) -> str:
        """Format deadline date for display."""
        if not deadline_date:
            return "N/A"
        
        return deadline_date.strftime("%Y-%m-%d")
    
    def _generate_tender_html(self, tender: Dict[str, Any]) -> str:
        """Generate HTML for a single tender."""
        return f"""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #f9f9f9;">
            <h3 style="margin: 0 0 8px 0; color: #333;">
                <a href="{tender['url']}" style="color: #0066cc; text-decoration: none;">{tender['title']}</a>
            </h3>
            <div style="margin-bottom: 8px;">
                <strong>Buyer:</strong> {tender.get('buyer_name', 'N/A')}<br>
                <strong>Country:</strong> {tender.get('buyer_country', 'N/A')}<br>
                <strong>Deadline:</strong> {self._format_deadline(tender.get('deadline_date'))}<br>
                <strong>CPV Codes:</strong> {self._format_cpv_codes(tender.get('cpv_codes', []))}<br>
                <strong>Est. Value:</strong> {self._format_currency(tender.get('value_amount'), tender.get('currency'))}
            </div>
            {f'<p style="margin: 8px 0 0 0; color: #666; font-size: 14px;">{tender.get("summary", "")}</p>' if tender.get("summary") else ""}
        </div>
        """
    
    def _generate_tender_text(self, tender: Dict[str, Any]) -> str:
        """Generate text for a single tender."""
        return f"""
{tender['title']}
URL: {tender['url']}
Buyer: {tender.get('buyer_name', 'N/A')}
Country: {tender.get('buyer_country', 'N/A')}
Deadline: {self._format_deadline(tender.get('deadline_date'))}
CPV Codes: {self._format_cpv_codes(tender.get('cpv_codes', []))}
Est. Value: {self._format_currency(tender.get('value_amount'), tender.get('currency'))}
{f'Summary: {tender.get("summary", "")}' if tender.get("summary") else ""}

---
"""
    
    def _generate_email_html(
        self,
        filter_name: str,
        tenders: List[Dict[str, Any]],
        user_email: str,
    ) -> str:
        """Generate HTML email content."""
        tender_count = len(tenders)
        tender_html = "\n".join(self._generate_tender_html(tender) for tender in tenders)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Tenders - {filter_name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #003399; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; position: relative;">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8Y2lyY2xlIGN4PSIxNiIgY3k9IjE2IiByPSIxNiIgZmlsbD0iIzAwMzM5OSIvPgogIDxnIHN0cm9rZT0iI0ZGQ0MwMCIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgZmlsbD0ibm9uZSI+CiAgICA8cGF0aCBkPSJNNiAxNiBMMTAgMTYgTDEyIDEwIEwxNiAyMiBMMTggNiBMMjAgMTYgTDI2IDE2IiBvcGFjaXR5PSIxIi8+CiAgICA8cGF0aCBkPSJNOCAyMCBMMTAgMjAgTDEyIDE4IEwxNCAyMiBMMTYgMTggTDE4IDIwIEwyNCAyMCIgb3BhY2l0eT0iMC42IiBzdHJva2Utd2lkdGg9IjIiLz4KICA8L2c+CiAgPGcgZmlsbD0iI0ZGQ0MwMCIgb3BhY2l0eT0iMC45Ij4KICAgIDxjaXJjbGUgY3g9IjgiIGN5PSI4IiByPSIxIi8+CiAgICA8Y2lyY2xlIGN4PSIyNCIgY3k9IjgiIHI9IjEiLz4KICA8L2c+Cjwvc3ZnPg==" alt="TenderPulse" style="width: 32px; height: 32px; position: absolute; left: 20px; top: 50%; transform: translateY(-50%);">
                <h1 style="margin: 0; font-size: 24px; font-family: 'Manrope', sans-serif;">TenderPulse</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">[TenderPulse] New tenders for: {filter_name}</p>
            </div>
            
            <div style="background-color: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="font-size: 16px; margin: 0 0 20px 0;">
                    We found <strong>{tender_count}</strong> new tender{tender_count != 1 and 's' or ''} matching your criteria.
                </p>
                
                {tender_html}
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center;">
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        <a href="#" style="color: #0066cc;">Manage your alerts</a> | 
                        <a href="#" style="color: #0066cc;">Unsubscribe</a>
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 8px 0 0 0;">
                        This email was sent to {user_email} because you have an active alert for "{filter_name}".
                    </p>
                    <p style="color: #999; font-size: 11px; margin: 4px 0 0 0;">
                        TenderPulse is an independent service and is not affiliated with the European Union or its institutions.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_email_text(
        self,
        filter_name: str,
        tenders: List[Dict[str, Any]],
        user_email: str,
    ) -> str:
        """Generate text email content."""
        tender_count = len(tenders)
        tender_text = "\n".join(self._generate_tender_text(tender) for tender in tenders)
        
        return f"""
PROCUREMENT COPILOT
New tenders for: {filter_name}

We found {tender_count} new tender{tender_count != 1 and 's' or ''} matching your criteria.

{tender_text}

---
Manage your alerts: [placeholder link]
Unsubscribe: [placeholder link]

This email was sent to {user_email} because you have an active alert for "{filter_name}".
        """.strip()
    
    async def send_tender_digest(
        self,
        user_email: str,
        filter_name: str,
        tenders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Send tender digest email."""
        if not tenders:
            self.logger.info(f"No tenders to send for filter '{filter_name}' to {user_email}")
            return {"status": "skipped", "reason": "no_tenders"}
        
        tender_count = len(tenders)
        subject = f"[Procurement Copilot] New tenders for: {filter_name} ({tender_count})"
        
        html_content = self._generate_email_html(filter_name, tenders, user_email)
        text_content = self._generate_email_text(filter_name, tenders, user_email)
        
        try:
            result = await self.provider.send_email(
                to=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
            
            self.logger.info(f"Tender digest sent to {user_email}: {tender_count} tenders")
            return {
                "status": "sent",
                "email_id": result.get("id"),
                "tender_count": tender_count,
            }
            
        except EmailError as e:
            self.logger.error(f"Failed to send tender digest to {user_email}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tender_count": tender_count,
            }
    
    def get_body_preview(self, tenders: List[Dict[str, Any]]) -> str:
        """Get email body preview (first 200 characters)."""
        if not tenders:
            return "No new tenders found."
        
        first_tender = tenders[0]
        preview = f"New tender: {first_tender['title']}"
        
        if len(tenders) > 1:
            preview += f" (+{len(tenders) - 1} more)"
        
        return preview[:200]


# Global email service instance
email_service = EmailService()
