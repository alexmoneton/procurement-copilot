"""
TED awards discovery system for finding lost bidders.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..db.models_outbound import Prospect, ProspectStatus
from ..db.models import TenderAward  # Assuming this exists in your models
from .utils import normalize_company, calculate_fit_score, now_paris

logger = logging.getLogger(__name__)


class AwardNotice:
    """Data class for award notice information."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.title = data.get('title', '')
        self.description = data.get('description', '')
        self.cpv_codes = data.get('cpv_codes', [])
        self.country = data.get('country', '')
        self.value_amount = data.get('value_amount', 0)
        self.currency = data.get('currency', 'EUR')
        self.deadline = data.get('deadline')
        self.buyer_name = data.get('buyer_name', '')
        self.winners = data.get('winners', [])
        self.bidders = data.get('bidders', [])
        self.publication_date = data.get('publication_date')
        self.award_date = data.get('award_date')


class TEDDiscovery:
    """TED awards discovery system."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def fetch_awards_since(self, since_dt: datetime) -> List[AwardNotice]:
        """
        Fetch TED awards published since given datetime.
        
        Args:
            since_dt: Datetime to fetch awards since
            
        Returns:
            List of AwardNotice objects
        """
        try:
            # Query database for recent awards
            # This assumes you have a TenderAward model
            query = select(TenderAward).where(
                TenderAward.publication_date >= since_dt
            ).order_by(TenderAward.publication_date.desc())
            
            result = await self.db.execute(query)
            awards = result.scalars().all()
            
            award_notices = []
            for award in awards:
                award_data = {
                    'id': award.id,
                    'title': award.title,
                    'description': award.description,
                    'cpv_codes': award.cpv_codes or [],
                    'country': award.country,
                    'value_amount': award.value_amount,
                    'currency': award.currency,
                    'deadline': award.deadline,
                    'buyer_name': award.buyer_name,
                    'winners': award.winners or [],
                    'bidders': award.bidders or [],
                    'publication_date': award.publication_date,
                    'award_date': award.award_date
                }
                award_notices.append(AwardNotice(award_data))
            
            self.logger.info(f"Fetched {len(award_notices)} awards since {since_dt}")
            return award_notices
            
        except Exception as e:
            self.logger.error(f"Error fetching awards: {e}")
            return []
    
    def infer_lost_bidders(self, award: AwardNotice) -> List[Dict[str, Any]]:
        """
        Infer lost bidders from award notice.
        
        Args:
            award: AwardNotice object
            
        Returns:
            List of lost bidder dictionaries
        """
        lost_bidders = []
        
        try:
            # If we have explicit winner and bidder lists
            if award.winners and award.bidders:
                winners_set = {normalize_company(w) for w in award.winners}
                
                for bidder in award.bidders:
                    normalized_bidder = normalize_company(bidder)
                    if normalized_bidder not in winners_set:
                        lost_bidders.append({
                            'company_name': bidder,
                            'normalized_company': normalized_bidder,
                            'country': award.country,
                            'cpv_family': self._extract_cpv_family(award.cpv_codes),
                            'last_award_ref': award.id,
                            'award_value': award.value_amount,
                            'award_currency': award.currency,
                            'buyer_name': award.buyer_name,
                            'publication_date': award.publication_date
                        })
            
            # If we only have winners, try to find similar companies
            elif award.winners:
                # This is a heuristic approach - in practice you might want to
                # query for companies in the same CPV/country that bid on similar tenders
                lost_bidders.extend(self._find_similar_bidders(award))
            
            # If no explicit bidder info, use heuristics
            else:
                lost_bidders.extend(self._find_potential_bidders(award))
            
            self.logger.info(f"Inferred {len(lost_bidders)} lost bidders from award {award.id}")
            return lost_bidders
            
        except Exception as e:
            self.logger.error(f"Error inferring lost bidders for award {award.id}: {e}")
            return []
    
    def _extract_cpv_family(self, cpv_codes: List[str]) -> str:
        """
        Extract CPV family from CPV codes.
        
        Args:
            cpv_codes: List of CPV codes
            
        Returns:
            CPV family string
        """
        if not cpv_codes:
            return "unknown"
        
        # Take the first CPV code and extract the family (first 2 digits)
        first_cpv = cpv_codes[0]
        if len(first_cpv) >= 2:
            return first_cpv[:2] + "000000-0"  # Convert to family format
        
        return "unknown"
    
    def _find_similar_bidders(self, award: AwardNotice) -> List[Dict[str, Any]]:
        """
        Find similar bidders using heuristics.
        
        Args:
            award: AwardNotice object
            
        Returns:
            List of potential lost bidder dictionaries
        """
        # This is a simplified heuristic - in practice you might want to:
        # 1. Query for companies that bid on similar CPV codes
        # 2. Look for companies in the same country
        # 3. Check for companies that bid on tenders from the same buyer
        
        # For now, return empty list - this would need more sophisticated logic
        return []
    
    def _find_potential_bidders(self, award: AwardNotice) -> List[Dict[str, Any]]:
        """
        Find potential bidders using heuristics.
        
        Args:
            award: AwardNotice object
            
        Returns:
            List of potential bidder dictionaries
        """
        # This is a simplified heuristic - in practice you might want to:
        # 1. Query for companies that typically bid on this CPV family
        # 2. Look for companies in the same country
        # 3. Check for companies that bid on tenders from the same buyer
        
        # For now, return empty list - this would need more sophisticated logic
        return []
    
    async def upsert_prospects(
        self, 
        lost_bidders: List[Dict[str, Any]], 
        min_score: float = 0.55
    ) -> int:
        """
        Upsert prospects into database.
        
        Args:
            lost_bidders: List of lost bidder dictionaries
            min_score: Minimum fit score threshold
            
        Returns:
            Number of prospects upserted
        """
        upserted_count = 0
        
        try:
            for bidder in lost_bidders:
                # Calculate fit score
                score = self._calculate_prospect_score(bidder)
                
                if score < min_score:
                    continue
                
                # Check if prospect already exists
                existing_query = select(Prospect).where(
                    and_(
                        Prospect.normalized_company == bidder['normalized_company'],
                        Prospect.country == bidder['country'],
                        Prospect.cpv_family == bidder['cpv_family'],
                        Prospect.last_award_ref == bidder['last_award_ref']
                    )
                )
                
                result = await self.db.execute(existing_query)
                existing_prospect = result.scalar_one_or_none()
                
                if existing_prospect:
                    # Update existing prospect
                    existing_prospect.score = score
                    existing_prospect.updated_at = datetime.utcnow()
                    if existing_prospect.status == ProspectStatus.NEW:
                        existing_prospect.status = ProspectStatus.ENRICHED
                else:
                    # Create new prospect
                    new_prospect = Prospect(
                        company_name=bidder['company_name'],
                        normalized_company=bidder['normalized_company'],
                        country=bidder['country'],
                        cpv_family=bidder['cpv_family'],
                        last_award_ref=bidder['last_award_ref'],
                        score=score,
                        status=ProspectStatus.NEW
                    )
                    self.db.add(new_prospect)
                
                upserted_count += 1
            
            await self.db.commit()
            self.logger.info(f"Upserted {upserted_count} prospects")
            return upserted_count
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error upserting prospects: {e}")
            return 0
    
    def _calculate_prospect_score(self, bidder: Dict[str, Any]) -> float:
        """
        Calculate fit score for a prospect.
        
        Args:
            bidder: Bidder dictionary
            
        Returns:
            Fit score between 0.0 and 1.0
        """
        # Calculate recency (days since publication)
        recency_days = 0
        if bidder.get('publication_date'):
            recency_days = (datetime.utcnow() - bidder['publication_date']).days
        
        # Determine if value is in SME range (€10K - €1M)
        value_in_sme_range = False
        if bidder.get('award_value'):
            value = bidder['award_value']
            if 10000 <= value <= 1000000:
                value_in_sme_range = True
        
        # For now, assume all prospects have CPV match and country focus
        # In practice, you might want to check against prospect's known focus areas
        cpv_match = True
        country_focus = True
        
        return calculate_fit_score(
            cpv_match=cpv_match,
            value_in_sme_range=value_in_sme_range,
            country_focus=country_focus,
            recency_days=recency_days
        )
    
    async def discover_prospects(
        self, 
        days: int = 1, 
        min_score: float = 0.55
    ) -> Dict[str, int]:
        """
        Discover prospects from recent TED awards.
        
        Args:
            days: Number of days to look back
            min_score: Minimum fit score threshold
            
        Returns:
            Dictionary with discovery statistics
        """
        try:
            # Calculate since datetime
            since_dt = now_paris() - timedelta(days=days)
            
            # Fetch awards
            awards = await self.fetch_awards_since(since_dt)
            
            # Infer lost bidders
            all_lost_bidders = []
            for award in awards:
                lost_bidders = self.infer_lost_bidders(award)
                all_lost_bidders.extend(lost_bidders)
            
            # Upsert prospects
            upserted_count = await self.upsert_prospects(all_lost_bidders, min_score)
            
            return {
                'awards_processed': len(awards),
                'lost_bidders_found': len(all_lost_bidders),
                'prospects_upserted': upserted_count,
                'since_datetime': since_dt.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in prospect discovery: {e}")
            return {
                'awards_processed': 0,
                'lost_bidders_found': 0,
                'prospects_upserted': 0,
                'error': str(e)
            }
