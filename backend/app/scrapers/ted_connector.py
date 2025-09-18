"""TED connector implementing the Connector protocol."""

import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import random

from loguru import logger

from .base import Connector, RawNotice


class TEDConnector:
    """TED (Tenders Electronic Daily) connector."""
    
    @property
    def name(self) -> str:
        return "TED (Tenders Electronic Daily)"
    
    @property
    def source(self) -> str:
        return "TED"
    
    async def fetch_since(self, since: datetime, limit: Optional[int] = None) -> List[RawNotice]:
        """Fetch TED notices published since the given datetime."""
        logger.info(f"Fetching TED notices since {since}")
        
        try:
            # For MVP, generate realistic TED data
            # In production, this would call the actual TED API
            notices = await self._generate_realistic_ted_notices(since, limit or 100)
            logger.info(f"Generated {len(notices)} TED notices")
            return notices
            
        except Exception as e:
            logger.error(f"Error fetching TED notices: {e}")
            return []
    
    async def _generate_realistic_ted_notices(self, since: datetime, limit: int) -> List[RawNotice]:
        """Generate realistic TED notices for MVP."""
        
        # European countries and buyers
        eu_buyers = [
            {"country": "DE", "buyer": "Bundesministerium für Digitales und Verkehr"},
            {"country": "FR", "buyer": "Ministère de l'Économie et des Finances"},
            {"country": "IT", "buyer": "Ministero dello Sviluppo Economico"},
            {"country": "ES", "buyer": "Ministerio de Hacienda"},
            {"country": "NL", "buyer": "Ministerie van Infrastructuur en Waterstaat"},
            {"country": "PL", "buyer": "Ministerstwo Rozwoju i Technologii"},
            {"country": "BE", "buyer": "Service Public Fédéral Économie"},
            {"country": "AT", "buyer": "Bundesministerium für Digitalisierung"},
            {"country": "SE", "buyer": "Regeringskansliet"},
            {"country": "DK", "buyer": "Erhvervsministeriet"},
        ]
        
        # Realistic procurement sectors
        sectors = [
            ("Digital transformation services", ["72000000", "79400000"], 450000, 2500000),
            ("Infrastructure development", ["45000000", "71000000"], 800000, 15000000),
            ("Healthcare technology solutions", ["33100000", "72200000"], 200000, 3000000),
            ("Environmental services", ["90000000", "77300000"], 150000, 1800000),
            ("Education and training services", ["80000000", "79600000"], 100000, 800000),
            ("Energy efficiency projects", ["09310000", "45300000"], 600000, 8000000),
            ("Transportation systems", ["60000000", "34600000"], 1000000, 12000000),
            ("IT security and cybersecurity", ["72500000", "79714000"], 300000, 2000000),
            ("Research and development", ["73000000", "73100000"], 250000, 5000000),
            ("Public building construction", ["45210000", "45400000"], 2000000, 25000000),
        ]
        
        notices = []
        base_date = since.date()
        
        for i in range(limit):
            # Select buyer and sector
            buyer_info = eu_buyers[i % len(eu_buyers)]
            sector_name, cpv_codes, min_val, max_val = sectors[i % len(sectors)]
            
            # Generate dates (published since the 'since' date)
            days_since = random.randint(0, 7)  # Published in last week
            pub_date = base_date + timedelta(days=days_since)
            deadline_days = random.randint(25, 60)
            deadline_date = pub_date + timedelta(days=deadline_days)
            
            # Generate value
            value_amount = random.randint(min_val, max_val)
            
            notice = RawNotice(
                tender_ref=f"TED-{datetime.now().year}-{(100000 + i):06d}",
                title=f"{sector_name} - {buyer_info['country']} Public Procurement",
                summary=f"Public procurement for {sector_name.lower()} in {buyer_info['country']}. This tender covers comprehensive services including planning, implementation, and maintenance of modern solutions for European public administration.",
                publication_date=pub_date.isoformat(),
                deadline_date=deadline_date.isoformat(),
                cpv_codes=cpv_codes,
                buyer_name=buyer_info["buyer"],
                buyer_country=buyer_info["country"],
                value_amount=float(value_amount),
                currency="EUR",
                url=f"https://ted.europa.eu/notice/{datetime.now().year}-{100000 + i}",
                raw_data={
                    "source": "TED",
                    "generated": True,
                    "sector": sector_name,
                    "cpv_primary": cpv_codes[0] if cpv_codes else None,
                    "tender_type": "public_procurement",
                    "procedure_type": "open",
                }
            )
            
            notices.append(notice)
        
        return notices


# Global connector instance
ted_connector = TEDConnector()
