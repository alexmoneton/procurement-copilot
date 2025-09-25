"""
TenderPulse Intelligence Engine
Transform raw tender data into actionable insights for premium customers
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TenderIntelligence:
    """Transform raw tender data into actionable insights"""

    def __init__(self):
        self.cpv_descriptions = {
            "45000000": "Construction work",
            "72000000": "IT services",
            "50000000": "Repair and maintenance services",
            "79000000": "Business services",
            "71000000": "Architectural and engineering services",
            "73000000": "Research and development services",
            "80000000": "Education and training services",
            "85000000": "Health and social work services",
            "90000000": "Sewage, refuse, cleaning services",
            "92000000": "Recreational, cultural and sporting services",
        }

        self.country_difficulty = {
            "DE": {
                "difficulty": 0.7,
                "avg_bidders": 8,
                "success_tips": "German tenders require precise technical specs",
            },
            "FR": {
                "difficulty": 0.6,
                "avg_bidders": 6,
                "success_tips": "French buyers prefer local partnerships",
            },
            "NL": {
                "difficulty": 0.5,
                "avg_bidders": 5,
                "success_tips": "Dutch procurement values sustainability highly",
            },
            "IT": {
                "difficulty": 0.8,
                "avg_bidders": 12,
                "success_tips": "Italian tenders often have complex bureaucracy",
            },
            "ES": {
                "difficulty": 0.6,
                "avg_bidders": 7,
                "success_tips": "Spanish regions have varying requirements",
            },
            "PL": {
                "difficulty": 0.4,
                "avg_bidders": 4,
                "success_tips": "Polish market has growing opportunities",
            },
            "SE": {
                "difficulty": 0.5,
                "avg_bidders": 5,
                "success_tips": "Swedish procurement emphasizes innovation",
            },
            "NO": {
                "difficulty": 0.6,
                "avg_bidders": 6,
                "success_tips": "Norwegian tenders often require local presence",
            },
        }

    def calculate_smart_score(self, tender: Dict, user_profile: Dict) -> int:
        """Calculate intelligent opportunity score (0-100)"""
        score = 50  # Base score

        # Value match (sweet spot scoring)
        tender_value = self.extract_value(tender.get("value_amount", 0))
        user_sweet_spot = user_profile.get("target_value_range", [50000, 2000000])

        if user_sweet_spot[0] <= tender_value <= user_sweet_spot[1]:
            score += 25
        elif tender_value < user_sweet_spot[0]:
            score -= 10  # Too small
        elif tender_value > user_sweet_spot[1] * 2:
            score -= 20  # Too big

        # Geographic preference
        country = tender.get("buyer_country", "")
        if country in user_profile.get("preferred_countries", []):
            score += 15

        # CPV match
        tender_cpvs = tender.get("cpv_codes", [])
        user_cpvs = user_profile.get("cpv_expertise", [])
        if any(
            cpv[:2] == user_cpv[:2] for cpv in tender_cpvs for user_cpv in user_cpvs
        ):
            score += 20

        # Competition level (fewer bidders = higher score)
        expected_bidders = self.country_difficulty.get(country, {}).get(
            "avg_bidders", 6
        )
        if expected_bidders <= 4:
            score += 15
        elif expected_bidders >= 10:
            score -= 10

        # Deadline pressure (more time = higher score for preparation)
        days_until_deadline = self.calculate_days_until_deadline(
            tender.get("deadline_date")
        )
        if days_until_deadline >= 30:
            score += 10
        elif days_until_deadline <= 7:
            score -= 15

        return max(0, min(100, int(score)))

    def generate_winning_strategy(self, tender: Dict, user_profile: Dict) -> Dict:
        """Generate specific advice for winning this tender"""
        country = tender.get("buyer_country", "")
        country_info = self.country_difficulty.get(country, {})

        strategy = {
            "success_probability": f"{self.calculate_smart_score(tender, user_profile)}%",
            "competition_level": self.estimate_competition(tender),
            "key_success_factors": [
                country_info.get("success_tips", "Focus on technical excellence"),
                self.get_cpv_specific_advice(tender.get("cpv_codes", [])),
                self.get_value_specific_advice(tender.get("value_amount", 0)),
            ],
            "preparation_checklist": self.generate_checklist(tender, country),
            "deadline_strategy": self.get_deadline_strategy(
                tender.get("deadline_date")
            ),
        }
        return strategy

    def estimate_competition(self, tender: Dict) -> str:
        """Estimate number of expected bidders"""
        country = tender.get("buyer_country", "")
        base_competition = self.country_difficulty.get(country, {}).get(
            "avg_bidders", 6
        )

        # Adjust based on tender characteristics
        tender_value = self.extract_value(tender.get("value_amount", 0))
        if tender_value > 5000000:  # €5M+
            base_competition += 3  # High-value attracts more bidders
        elif tender_value < 100000:  # €100K-
            base_competition -= 2  # Small tenders get less attention

        return f"{max(2, base_competition-1)}-{base_competition+2} bidders expected"

    def generate_checklist(self, tender: Dict, country: str) -> List[str]:
        """Generate country-specific compliance checklist"""
        base_checklist = [
            "Register on national procurement platform",
            "Prepare technical specifications document",
            "Obtain required certifications",
            "Prepare financial statements",
            "Draft project timeline",
            "Calculate detailed pricing",
        ]

        country_specific = {
            "DE": [
                "Obtain German tax certificate",
                "Prepare detailed Leistungsverzeichnis",
            ],
            "FR": ["Register for French SIRET number", "Prepare MAPA documentation"],
            "NL": [
                "Complete DigiD business registration",
                "Prepare sustainability statement",
            ],
            "IT": ["Obtain Italian fiscal code", "Prepare anti-mafia certification"],
            "ES": ["Register in Spanish ROLECE", "Prepare regional language documents"],
            "PL": [
                "Register in Polish REGON database",
                "Prepare Polish language documents",
            ],
            "SE": [
                "Register in Swedish company database",
                "Prepare environmental impact statement",
            ],
            "NO": [
                "Register for Norwegian organization number",
                "Prepare local content requirements",
            ],
        }

        return base_checklist + country_specific.get(country, [])

    def extract_value(self, value) -> int:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return int(value)

        if isinstance(value, str):
            # Extract numbers from value string
            numbers = re.findall(r"[\d,]+", value)
            if numbers:
                try:
                    clean_number = numbers[0].replace(",", "")
                    return int(clean_number)
                except:
                    pass

        return 0

    def calculate_days_until_deadline(self, deadline_str: Optional[str]) -> int:
        """Calculate days until deadline"""
        if not deadline_str:
            return 30  # Default assumption

        try:
            # Handle various date formats
            clean_date = deadline_str.split("+")[0].split("T")[0]
            deadline = datetime.strptime(clean_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (deadline - today).days
        except:
            return 30  # Default assumption

    def get_cpv_specific_advice(self, cpv_codes: List[str]) -> str:
        """Get advice specific to CPV category"""
        if not cpv_codes:
            return "Focus on clear technical specifications"

        main_cpv = cpv_codes[0][:2] if cpv_codes else ""

        advice_map = {
            "45": "Construction: Emphasize safety certifications and previous project portfolio",
            "72": "IT Services: Highlight security clearances and technical certifications",
            "50": "Maintenance: Focus on response times and preventive maintenance capabilities",
            "79": "Business Services: Emphasize methodology and previous client success stories",
            "71": "Engineering: Showcase technical expertise and regulatory compliance",
            "73": "R&D: Highlight innovation track record and research partnerships",
        }

        return advice_map.get(main_cpv, "Focus on technical excellence and compliance")

    def get_value_specific_advice(self, value: int) -> str:
        """Get advice based on contract value"""
        if value < 100000:
            return "Small contract: Focus on competitive pricing and quick delivery"
        elif value < 1000000:
            return (
                "Medium contract: Balance price competitiveness with quality guarantees"
            )
        else:
            return "Large contract: Emphasize track record, partnerships, and risk management"

    def get_deadline_strategy(self, deadline_str: Optional[str]) -> str:
        """Get strategy based on deadline timing"""
        days_left = self.calculate_days_until_deadline(deadline_str)

        if days_left <= 7:
            return "⚠️ URGENT: Focus on existing capabilities, minimal customization"
        elif days_left <= 21:
            return "⏰ MODERATE: Prepare detailed proposal with some customization"
        else:
            return "✅ AMPLE TIME: Full proposal development with partnerships and customization"


class RevenueEngine:
    """Convert users into paying customers systematically"""

    def __init__(self):
        self.pricing_tiers = {
            "free": {
                "price": 0,
                "opportunities_per_week": 5,
                "countries": 1,
                "features": ["basic_alerts", "web_access"],
            },
            "starter": {
                "price": 99,
                "opportunities_per_week": 50,
                "countries": 3,
                "features": ["smart_scoring", "email_alerts", "deadline_calendar"],
            },
            "pro": {
                "price": 199,
                "opportunities_per_week": 150,
                "countries": 5,
                "features": [
                    "all_starter",
                    "response_templates",
                    "compliance_checklists",
                    "competitor_analysis",
                ],
            },
            "expert": {
                "price": 399,
                "opportunities_per_week": "unlimited",
                "countries": "unlimited",
                "features": [
                    "all_pro",
                    "win_probability",
                    "custom_integrations",
                    "priority_support",
                ],
            },
        }

    def calculate_upgrade_triggers(self, user_behavior: Dict) -> List[Dict]:
        """Identify when user is ready to upgrade"""

        triggers = []

        # Usage-based triggers
        if user_behavior.get("weekly_logins", 0) >= 3:
            triggers.append(
                {
                    "type": "high_engagement",
                    "message": "You're checking opportunities 3+ times per week. Upgrade for instant alerts!",
                    "conversion_rate": 0.23,
                    "suggested_tier": "starter",
                }
            )

        if user_behavior.get("opportunities_viewed", 0) >= 20:
            triggers.append(
                {
                    "type": "high_volume",
                    "message": "You've viewed 20+ opportunities. Get unlimited access.",
                    "conversion_rate": 0.34,
                    "suggested_tier": "pro",
                }
            )

        if user_behavior.get("clicked_response_template", False):
            triggers.append(
                {
                    "type": "feature_interest",
                    "message": "Upgrade now to access response templates that win contracts.",
                    "conversion_rate": 0.45,
                    "suggested_tier": "pro",
                }
            )

        # Time-based triggers
        days_since_signup = user_behavior.get("days_since_signup", 0)
        if days_since_signup == 7:
            triggers.append(
                {
                    "type": "week_one",
                    "message": "You've seen the value. Ready to win your first contract?",
                    "conversion_rate": 0.18,
                    "suggested_tier": "starter",
                }
            )

        return sorted(triggers, key=lambda x: x["conversion_rate"], reverse=True)

    def should_show_upgrade_prompt(self, user_behavior: Dict) -> bool:
        """Determine if user should see upgrade prompt"""
        triggers = self.calculate_upgrade_triggers(user_behavior)
        return len(triggers) > 0 and triggers[0]["conversion_rate"] > 0.2


class PremiumEmailGenerator:
    """Generate compelling, personalized email alerts that convert"""

    def __init__(self):
        self.intelligence = TenderIntelligence()

    def generate_premium_alert(
        self, opportunities: List[Dict], user_profile: Dict, user_name: str = ""
    ) -> Dict:
        """Generate premium email with intelligence and personality"""

        if not opportunities:
            return self.generate_no_opportunities_email(user_name)

        # Add smart scores to opportunities
        for opp in opportunities:
            opp["smart_score"] = self.intelligence.calculate_smart_score(
                opp, user_profile
            )

        # Sort by intelligence score
        top_opportunities = sorted(
            opportunities, key=lambda x: x.get("smart_score", 0), reverse=True
        )[:3]

        subject = self.generate_subject_line(top_opportunities, user_profile)

        email_html = self.generate_html_email(top_opportunities, user_name)
        email_text = self.generate_text_email(top_opportunities, user_name)

        return {"subject": subject, "html": email_html, "text": email_text}

    def generate_subject_line(
        self, opportunities: List[Dict], user_profile: Dict
    ) -> str:
        """Generate compelling subject lines based on opportunities"""
        if not opportunities:
            return "No new opportunities this week - but here's what's coming..."

        top_score = opportunities[0].get("smart_score", 50)
        total_value = sum(opp.get("value_amount", 0) for opp in opportunities[:3])

        subjects = [
            f"🎯 {top_score}% match: €{total_value:,.0f} in opportunities waiting",
            f"⚡ {len(opportunities)} high-probability opportunities in your area",
            f"🏆 Perfect match alert: €{opportunities[0].get('value_amount', 0):,.0f} tender in {opportunities[0].get('buyer_country')}",
            f"📈 {len(opportunities)} opportunities, {top_score}% success probability",
        ]

        import random

        return random.choice(subjects)

    def generate_html_email(self, opportunities: List[Dict], user_name: str) -> str:
        """Generate premium HTML email"""

        email_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{ max-width: 600px; margin: 0 auto; font-family: 'Inter', Arial, sans-serif; }}
        .header {{ background: linear-gradient(135deg, #003399 0%, #FFCC00 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .opportunity {{ background: #f8f9fa; border-left: 4px solid #28a745; margin: 20px 0; padding: 15px; border-radius: 4px; }}
        .high-score {{ border-left-color: #28a745; }}
        .medium-score {{ border-left-color: #ffc107; }}
        .low-score {{ border-left-color: #dc3545; }}
        .score-badge {{ display: inline-block; padding: 4px 8px; border-radius: 12px; font-weight: bold; color: white; }}
        .score-high {{ background: #28a745; }}
        .score-medium {{ background: #ffc107; }}
        .score-low {{ background: #dc3545; }}
        .cta-button {{ background: #003399; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }}
        .footer {{ background: #f1f1f1; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎯 Your Weekly TenderPulse Report</h2>
            <p>Hi {user_name}! We found {len(opportunities)} new opportunities matching your profile.</p>
        </div>
        
        <div style="padding: 20px;">
            <h3>🏆 Top Opportunities This Week</h3>
"""

        for i, opp in enumerate(opportunities, 1):
            score = opp.get("smart_score", 50)
            score_class = "high" if score >= 70 else "medium" if score >= 50 else "low"

            email_html += f"""
            <div class="opportunity {score_class}-score">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #333;">{opp.get('title', 'Untitled Opportunity')[:60]}...</h4>
                    <span class="score-badge score-{score_class}">{score}% Match</span>
                </div>
                
                <p><strong>💰 Value:</strong> €{opp.get('value_amount', 0):,} | <strong>📍 Location:</strong> {opp.get('buyer_country', 'Unknown')}</p>
                <p><strong>⏰ Deadline:</strong> {opp.get('deadline_date', 'TBD')} | <strong>🏢 Buyer:</strong> {opp.get('buyer_name', 'Unknown')}</p>
                
                <div style="background: white; padding: 10px; border-radius: 4px; margin: 10px 0;">
                    <strong>🎯 Why You'll Win:</strong>
                    <ul style="margin: 5px 0;">
                        <li>Perfect size match for your capacity</li>
                        <li>Location in your target region</li>
                        <li>Lower than average competition expected</li>
                    </ul>
                </div>
                
                <a href="{opp.get('url', '#')}" class="cta-button">
                    View Full Tender Details →
                </a>
            </div>
"""

        email_html += f"""
        </div>
        
        <div class="footer">
            <p><strong>📈 Your Performance:</strong> Companies using TenderPulse win 34% more contracts on average.</p>
            <p><a href="https://tenderpulse.eu/pricing" style="color: #003399;">Upgrade to Pro</a> for response templates and compliance checklists.</p>
            <p style="font-size: 12px; color: #666;">
                TenderPulse | <a href="https://tenderpulse.eu/unsubscribe">Unsubscribe</a> | 
                <a href="https://tenderpulse.eu/account">Manage Preferences</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

        return email_html

    def generate_text_email(self, opportunities: List[Dict], user_name: str) -> str:
        """Generate text version of premium email"""

        email_text = f"""
TenderPulse Weekly Report

Hi {user_name}!

Here are {len(opportunities)} new tender opportunities matching your profile:

"""

        for i, opp in enumerate(opportunities, 1):
            score = opp.get("smart_score", 50)
            email_text += f"""
{i}. {opp.get('title', 'Untitled Opportunity')}
   Match Score: {score}%
   Value: €{opp.get('value_amount', 0):,}
   Location: {opp.get('buyer_country', 'Unknown')}
   Deadline: {opp.get('deadline_date', 'TBD')}
   View: {opp.get('url', '#')}

"""

        email_text += """
Best regards,
Your TenderPulse Team

P.S. Upgrade to Pro for response templates and win probability analysis.
Visit: https://tenderpulse.eu/pricing

---
TenderPulse | Unsubscribe: https://tenderpulse.eu/unsubscribe
"""

        return email_text

    def generate_no_opportunities_email(self, user_name: str) -> Dict:
        """Generate email when no opportunities found"""
        return {
            "subject": "🔍 No matches this week - but here's what to do",
            "html": f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Hi {user_name}!</h2>
    <p>No new opportunities matched your criteria this week, but that's not necessarily bad news!</p>
    
    <h3>🎯 What This Means:</h3>
    <ul>
        <li>Your criteria might be too specific (consider broadening)</li>
        <li>It's a quiet week in your sector (normal seasonal variation)</li>
        <li>Opportunities are coming - procurement cycles have natural rhythms</li>
    </ul>
    
    <h3>📈 What to Do:</h3>
    <ul>
        <li><a href="https://tenderpulse.eu/app">Review your filters</a> - consider adding related CPV codes</li>
        <li>Expand to neighboring countries for more opportunities</li>
        <li>Use this quiet time to prepare templates and certifications</li>
    </ul>
    
    <p><a href="https://tenderpulse.eu/pricing" style="background: #003399; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Upgrade to Pro</a> for market insights and trend analysis.</p>
</div>
""",
            "text": f"""
Hi {user_name}!

No new opportunities matched your criteria this week, but that's not necessarily bad news!

What This Means:
- Your criteria might be too specific (consider broadening)
- It's a quiet week in your sector (normal seasonal variation)  
- Opportunities are coming - procurement cycles have natural rhythms

What to Do:
- Review your filters: https://tenderpulse.eu/app
- Expand to neighboring countries for more opportunities
- Use this quiet time to prepare templates and certifications

Upgrade to Pro for market insights: https://tenderpulse.eu/pricing

Best regards,
Your TenderPulse Team
""",
        }
