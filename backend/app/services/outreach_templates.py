"""Email templates for outreach campaigns."""

from typing import Dict, List, Any, Optional
from datetime import date
from loguru import logger


class OutreachTemplates:
    """Email templates for different outreach campaigns."""
    
    def __init__(self):
        self.logger = logger.bind(service="outreach_templates")
    
    def generate_missed_opportunities_email(
        self,
        company_name: str,
        sector: str,
        missed_tenders: List[Dict[str, Any]],
        upcoming_tenders: List[Dict[str, Any]],
        trial_link: str = "https://tenderpulse.eu/pricing"
    ) -> Dict[str, str]:
        """
        Email 1: Missed Opportunities
        Subject: "You missed 3 tenders in {sector} last month"
        """
        subject = f"You missed {len(missed_tenders)} tenders in {sector} last month"
        
        # Build missed tenders list
        missed_list = ""
        for tender in missed_tenders[:3]:  # Show max 3
            missed_list += f"• {tender.get('title', 'Unknown')} in {tender.get('country', 'Unknown')}\n"
        
        # Build upcoming tenders list
        upcoming_list = ""
        for tender in upcoming_tenders[:3]:  # Show max 3
            deadline = tender.get('deadline', 'Unknown')
            if isinstance(deadline, date):
                deadline = deadline.strftime('%B %d, %Y')
            upcoming_list += f"• {tender.get('title', 'Unknown')} (deadline {deadline})\n"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .tender-list {{ background-color: #f8fafc; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .cta {{ background-color: #2563eb; color: white; padding: 15px; text-align: center; margin: 20px 0; }}
                .cta a {{ color: white; text-decoration: none; font-weight: bold; }}
                .footer {{ background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; }}
                .unsubscribe {{ color: #64748b; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Procurement Copilot</h1>
                    <p>Never Miss Another Opportunity</p>
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
                        <a href="{trial_link}">Start Your Free Trial</a>
                    </div>
                    
                    <p>Our AI-powered system monitors 50,000+ tenders across Europe and sends personalized alerts directly to your inbox.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, <a href="#" class="unsubscribe">unsubscribe here</a>.</p>
                    <p>Procurement Copilot - AI-Powered Tender Monitoring</p>
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
        Start your free trial: {trial_link}
        
        Our AI-powered system monitors 50,000+ tenders across Europe and sends personalized alerts directly to your inbox.
        
        ---
        This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, unsubscribe here.
        TenderPulse - Real-time signals for public contracts
        Independent service; not affiliated with the EU.
        """
        
        return {
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content
        }
    
    def generate_cross_border_expansion_email(
        self,
        company_name: str,
        home_country: str,
        adjacent_country: str,
        upcoming_tenders: List[Dict[str, Any]],
        trial_link: str = "https://tenderpulse.eu/pricing"
    ) -> Dict[str, str]:
        """
        Email 2: Expand Cross-Border
        Subject: "You're strong in {home_country}. Here's what you're missing in {adjacent_country}"
        """
        subject = f"You're strong in {home_country}. Here's what you're missing in {adjacent_country}"
        
        # Build upcoming tenders list
        upcoming_list = ""
        for tender in upcoming_tenders[:5]:  # Show max 5
            deadline = tender.get('deadline', 'Unknown')
            if isinstance(deadline, date):
                deadline = deadline.strftime('%B %d, %Y')
            value = tender.get('value', 'Unknown')
            currency = tender.get('currency', 'EUR')
            if value and value != 'Unknown':
                value_str = f"€{value:,.0f}" if currency == 'EUR' else f"{value:,.0f} {currency}"
            else:
                value_str = "Value not specified"
            
            upcoming_list += f"• {tender.get('title', 'Unknown')}\n  Deadline: {deadline} | Value: {value_str}\n\n"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .tender-list {{ background-color: #f0fdf4; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .cta {{ background-color: #059669; color: white; padding: 15px; text-align: center; margin: 20px 0; }}
                .cta a {{ color: white; text-decoration: none; font-weight: bold; }}
                .footer {{ background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; }}
                .unsubscribe {{ color: #64748b; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Procurement Copilot</h1>
                    <p>Expand Your Business Across Borders</p>
                </div>
                
                <div class="content">
                    <h2>Hi {company_name},</h2>
                    
                    <p>We've noticed you're doing great in {home_country} with multiple successful bids. But did you know there are similar opportunities just across the border in {adjacent_country}?</p>
                    
                    <h3>Upcoming Tenders in {adjacent_country}:</h3>
                    <div class="tender-list">
                        <pre>{upcoming_list}</pre>
                    </div>
                    
                    <p>Cross-border tenders often have less competition and can be a great way to expand your business. Our platform makes it easy to monitor opportunities in neighboring countries.</p>
                    
                    <div class="cta">
                        <a href="{trial_link}">Start Monitoring {adjacent_country} Tenders</a>
                    </div>
                    
                    <p>Get alerts for tenders in {adjacent_country} that match your expertise and bidding history.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, <a href="#" class="unsubscribe">unsubscribe here</a>.</p>
                    <p>Procurement Copilot - AI-Powered Tender Monitoring</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {company_name},
        
        We've noticed you're doing great in {home_country} with multiple successful bids. But did you know there are similar opportunities just across the border in {adjacent_country}?
        
        Upcoming Tenders in {adjacent_country}:
        {upcoming_list}
        
        Cross-border tenders often have less competition and can be a great way to expand your business. Our platform makes it easy to monitor opportunities in neighboring countries.
        
        Start monitoring {adjacent_country} tenders: {trial_link}
        
        Get alerts for tenders in {adjacent_country} that match your expertise and bidding history.
        
        ---
        This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, unsubscribe here.
        TenderPulse - Real-time signals for public contracts
        Independent service; not affiliated with the EU.
        """
        
        return {
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content
        }
    
    def generate_reactivation_email(
        self,
        company_name: str,
        sector: str,
        upcoming_tenders: List[Dict[str, Any]],
        trial_link: str = "https://tenderpulse.eu/pricing"
    ) -> Dict[str, str]:
        """
        Email 3: Reactivation
        Subject: "Are you still bidding in {sector}? Here's a curated list for this month"
        """
        subject = f"Are you still bidding in {sector}? Here's a curated list for this month"
        
        # Build upcoming tenders list
        upcoming_list = ""
        for tender in upcoming_tenders[:5]:  # Show max 5
            deadline = tender.get('deadline', 'Unknown')
            if isinstance(deadline, date):
                deadline = deadline.strftime('%B %d, %Y')
            value = tender.get('value', 'Unknown')
            currency = tender.get('currency', 'EUR')
            if value and value != 'Unknown':
                value_str = f"€{value:,.0f}" if currency == 'EUR' else f"{value:,.0f} {currency}"
            else:
                value_str = "Value not specified"
            
            upcoming_list += f"• {tender.get('title', 'Unknown')}\n  Deadline: {deadline} | Value: {value_str}\n  Country: {tender.get('country', 'Unknown')}\n\n"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .tender-list {{ background-color: #fef2f2; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .cta {{ background-color: #dc2626; color: white; padding: 15px; text-align: center; margin: 20px 0; }}
                .cta a {{ color: white; text-decoration: none; font-weight: bold; }}
                .footer {{ background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; }}
                .unsubscribe {{ color: #64748b; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Procurement Copilot</h1>
                    <p>Don't Miss Out on Great Opportunities</p>
                </div>
                
                <div class="content">
                    <h2>Hi {company_name},</h2>
                    
                    <p>We noticed you haven't been bidding on {sector} tenders recently. Are you still active in this sector? We've curated some great opportunities for you this month.</p>
                    
                    <h3>This Month's {sector} Opportunities:</h3>
                    <div class="tender-list">
                        <pre>{upcoming_list}</pre>
                    </div>
                    
                    <p>These tenders match your previous bidding patterns and could be perfect for your business.</p>
                    
                    <div class="cta">
                        <a href="{trial_link}">Get Back in the Game</a>
                    </div>
                    
                    <p>Don't let great opportunities pass you by. Our platform can help you stay on top of relevant tenders with personalized alerts.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, <a href="#" class="unsubscribe">unsubscribe here</a>.</p>
                    <p>Procurement Copilot - AI-Powered Tender Monitoring</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {company_name},
        
        We noticed you haven't been bidding on {sector} tenders recently. Are you still active in this sector? We've curated some great opportunities for you this month.
        
        This Month's {sector} Opportunities:
        {upcoming_list}
        
        These tenders match your previous bidding patterns and could be perfect for your business.
        
        Get back in the game: {trial_link}
        
        Don't let great opportunities pass you by. Our platform can help you stay on top of relevant tenders with personalized alerts.
        
        ---
        This email was sent because you've been bidding on public tenders. If you no longer wish to receive these emails, unsubscribe here.
        TenderPulse - Real-time signals for public contracts
        Independent service; not affiliated with the EU.
        """
        
        return {
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content
        }
    
    def generate_unsubscribe_email(
        self,
        company_name: str,
        unsubscribe_link: str
    ) -> Dict[str, str]:
        """Generate unsubscribe confirmation email."""
        subject = "You've been unsubscribed from Procurement Copilot"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6b7280; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Procurement Copilot</h1>
                </div>
                
                <div class="content">
                    <h2>You've been unsubscribed</h2>
                    <p>Hi {company_name},</p>
                    <p>You have successfully unsubscribed from our outreach emails.</p>
                    <p>If you change your mind, you can always resubscribe by visiting our website.</p>
                    <p>Thank you for your time.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {company_name},
        
        You have successfully unsubscribed from our outreach emails.
        
        If you change your mind, you can always resubscribe by visiting our website.
        
        Thank you for your time.
        
        Procurement Copilot
        """
        
        return {
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content
        }


# Global templates instance
outreach_templates = OutreachTemplates()
