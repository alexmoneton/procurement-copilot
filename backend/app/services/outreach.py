"""Outreach service for targeting SME bidders based on public tender data."""

import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select, text

from ..db.models import Award, Company, Tender
from ..db.crud import AwardCRUD, CompanyCRUD
from ..db.schemas import CompanyCreate


class OutreachTargetingService:
    """Service for identifying and targeting SME bidders."""
    
    def __init__(self):
        self.logger = logger.bind(service="outreach_targeting")
    
    async def get_active_but_losing_smes(
        self,
        db: AsyncSession,
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Query #1: "Active but losing" SMEs
        Companies that appear in other_bidders >= 2 times in the last 6 months
        """
        self.logger.info("Finding active but losing SMEs")
        
        # Calculate date range (last 6 months)
        six_months_ago = date.today() - timedelta(days=180)
        
        # Build base query for awards in the last 6 months
        base_query = select(Award).where(Award.award_date >= six_months_ago)
        
        # Add filters if provided
        if cpv_codes:
            # Join with tenders to filter by CPV codes
            base_query = base_query.join(Tender, Award.tender_ref == Tender.tender_ref)
            cpv_conditions = []
            for cpv in cpv_codes:
                cpv_conditions.append(Tender.cpv_codes.contains([cpv]))
            base_query = base_query.where(or_(*cpv_conditions))
        
        if country:
            base_query = base_query.join(Tender, Award.tender_ref == Tender.tender_ref)
            base_query = base_query.where(Tender.buyer_country == country.upper())
        
        # Execute query to get awards
        result = await db.execute(base_query)
        awards = result.scalars().all()
        
        # Count appearances in other_bidders
        company_counts = {}
        for award in awards:
            if award.other_bidders:
                for bidder_name in award.other_bidders:
                    if bidder_name.strip():
                        company_counts[bidder_name] = company_counts.get(bidder_name, 0) + 1
        
        # Filter companies with >= 2 appearances
        losing_companies = [
            {"name": name, "bid_count": count}
            for name, count in company_counts.items()
            if count >= 2
        ]
        
        # Sort by bid count (descending) and limit
        losing_companies.sort(key=lambda x: x["bid_count"], reverse=True)
        losing_companies = losing_companies[:limit]
        
        self.logger.info(f"Found {len(losing_companies)} active but losing SMEs")
        return losing_companies
    
    async def get_single_country_bidders_with_cross_border_potential(
        self,
        db: AsyncSession,
        cpv_codes: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Query #2: "Single-country bidders with cross-border potential"
        Companies with >= 3 bids in one country and zero in neighbors, for same CPV family
        """
        self.logger.info("Finding single-country bidders with cross-border potential")
        
        # Calculate date range (last 12 months)
        twelve_months_ago = date.today() - timedelta(days=365)
        
        # Get all awards in the last 12 months
        awards_query = select(Award).where(Award.award_date >= twelve_months_ago)
        
        if cpv_codes:
            awards_query = awards_query.join(Tender, Award.tender_ref == Tender.tender_ref)
            cpv_conditions = []
            for cpv in cpv_codes:
                cpv_conditions.append(Tender.cpv_codes.contains([cpv]))
            awards_query = awards_query.where(or_(*cpv_conditions))
        
        result = await db.execute(awards_query)
        awards = result.scalars().all()
        
        # Get tender details for each award
        tender_refs = [award.tender_ref for award in awards]
        tenders_query = select(Tender).where(Tender.tender_ref.in_(tender_refs))
        tenders_result = await db.execute(tenders_query)
        tenders = {t.tender_ref: t for t in tenders_result.scalars().all()}
        
        # Analyze bidding patterns by company and country
        company_country_bids = {}
        
        for award in awards:
            tender = tenders.get(award.tender_ref)
            if not tender:
                continue
            
            country = tender.buyer_country
            
            # Count all bidders (winners and others)
            all_bidders = award.winner_names.copy()
            if award.other_bidders:
                all_bidders.extend(award.other_bidders)
            
            for bidder_name in all_bidders:
                if bidder_name.strip():
                    if bidder_name not in company_country_bids:
                        company_country_bids[bidder_name] = {}
                    
                    if country not in company_country_bids[bidder_name]:
                        company_country_bids[bidder_name][country] = 0
                    
                    company_country_bids[bidder_name][country] += 1
        
        # Find companies with >= 3 bids in one country and zero in neighbors
        cross_border_candidates = []
        
        for company_name, country_bids in company_country_bids.items():
            # Find countries with >= 3 bids
            strong_countries = [
                country for country, count in country_bids.items() 
                if count >= 3
            ]
            
            if not strong_countries:
                continue
            
            # For each strong country, check if they have zero bids in neighbors
            for strong_country in strong_countries:
                neighbor_countries = self._get_neighbor_countries(strong_country)
                
                # Check if they have any bids in neighbor countries
                has_neighbor_bids = any(
                    country_bids.get(neighbor, 0) > 0 
                    for neighbor in neighbor_countries
                )
                
                if not has_neighbor_bids:
                    cross_border_candidates.append({
                        "name": company_name,
                        "strong_country": strong_country,
                        "bid_count": country_bids[strong_country],
                        "neighbor_countries": neighbor_countries
                    })
        
        # Sort by bid count and limit
        cross_border_candidates.sort(key=lambda x: x["bid_count"], reverse=True)
        cross_border_candidates = cross_border_candidates[:limit]
        
        self.logger.info(f"Found {len(cross_border_candidates)} cross-border potential companies")
        return cross_border_candidates
    
    async def get_lapsed_bidders(
        self,
        db: AsyncSession,
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Query #3: "Lapsed bidders"
        Companies that bid frequently 12-6 months ago, but 6-0 months show zero activity
        """
        self.logger.info("Finding lapsed bidders")
        
        # Calculate date ranges
        twelve_months_ago = date.today() - timedelta(days=365)
        six_months_ago = date.today() - timedelta(days=180)
        
        # Get awards from 12-6 months ago (active period)
        active_period_query = select(Award).where(
            and_(
                Award.award_date >= twelve_months_ago,
                Award.award_date < six_months_ago
            )
        )
        
        # Get awards from 6-0 months ago (lapsed period)
        lapsed_period_query = select(Award).where(Award.award_date >= six_months_ago)
        
        # Add filters if provided
        if cpv_codes or country:
            active_period_query = active_period_query.join(Tender, Award.tender_ref == Tender.tender_ref)
            lapsed_period_query = lapsed_period_query.join(Tender, Award.tender_ref == Tender.tender_ref)
            
            conditions = []
            if cpv_codes:
                cpv_conditions = []
                for cpv in cpv_codes:
                    cpv_conditions.append(Tender.cpv_codes.contains([cpv]))
                conditions.append(or_(*cpv_conditions))
            
            if country:
                conditions.append(Tender.buyer_country == country.upper())
            
            if conditions:
                active_period_query = active_period_query.where(and_(*conditions))
                lapsed_period_query = lapsed_period_query.where(and_(*conditions))
        
        # Execute queries
        active_result = await db.execute(active_period_query)
        active_awards = active_result.scalars().all()
        
        lapsed_result = await db.execute(lapsed_period_query)
        lapsed_awards = lapsed_result.scalars().all()
        
        # Count bids in active period
        active_bidders = {}
        for award in active_awards:
            all_bidders = award.winner_names.copy()
            if award.other_bidders:
                all_bidders.extend(award.other_bidders)
            
            for bidder_name in all_bidders:
                if bidder_name.strip():
                    active_bidders[bidder_name] = active_bidders.get(bidder_name, 0) + 1
        
        # Count bids in lapsed period
        lapsed_bidders = set()
        for award in lapsed_awards:
            all_bidders = award.winner_names.copy()
            if award.other_bidders:
                all_bidders.extend(award.other_bidders)
            
            for bidder_name in all_bidders:
                if bidder_name.strip():
                    lapsed_bidders.add(bidder_name)
        
        # Find companies that were active but are now lapsed
        lapsed_candidates = []
        for company_name, bid_count in active_bidders.items():
            if bid_count >= 2 and company_name not in lapsed_bidders:
                lapsed_candidates.append({
                    "name": company_name,
                    "active_bid_count": bid_count,
                    "last_active_period": "12-6 months ago"
                })
        
        # Sort by bid count and limit
        lapsed_candidates.sort(key=lambda x: x["active_bid_count"], reverse=True)
        lapsed_candidates = lapsed_candidates[:limit]
        
        self.logger.info(f"Found {len(lapsed_candidates)} lapsed bidders")
        return lapsed_candidates
    
    def _get_neighbor_countries(self, country: str) -> List[str]:
        """Get neighboring countries for cross-border analysis."""
        # Simplified neighbor mapping for European countries
        neighbors = {
            "FR": ["ES", "IT", "DE", "BE", "LU", "CH", "AD", "MC"],
            "DE": ["FR", "BE", "NL", "DK", "PL", "CZ", "AT", "CH", "LU"],
            "ES": ["FR", "PT", "AD"],
            "IT": ["FR", "CH", "AT", "SI", "SM", "VA"],
            "NL": ["DE", "BE"],
            "BE": ["FR", "DE", "NL", "LU"],
            "PL": ["DE", "CZ", "SK", "LT", "BY", "UA"],
            "AT": ["DE", "CH", "IT", "SI", "HU", "SK", "CZ"],
            "CH": ["FR", "DE", "IT", "AT", "LI"],
            "PT": ["ES"],
            "SE": ["NO", "FI", "DK"],
            "DK": ["DE", "SE", "NO"],
            "FI": ["SE", "NO", "RU", "EE"],
            "NO": ["SE", "DK", "FI", "RU"],
            "CZ": ["DE", "AT", "SK", "PL"],
            "HU": ["AT", "SK", "UA", "RO", "RS", "HR", "SI"],
            "SK": ["CZ", "AT", "HU", "PL", "UA"],
            "SI": ["IT", "AT", "HU", "HR"],
            "HR": ["HU", "SI", "BA", "RS", "ME", "IT"],
            "RO": ["HU", "UA", "MD", "BG", "RS"],
            "BG": ["RO", "RS", "MK", "GR", "TR"],
            "EE": ["FI", "LV", "RU"],
            "LV": ["EE", "LT", "RU", "BY"],
            "LT": ["LV", "PL", "BY", "RU"],
            "IE": ["GB"],
            "LU": ["FR", "DE", "BE"],
        }
        
        return neighbors.get(country.upper(), [])
    
    async def get_upcoming_tenders_for_company(
        self,
        db: AsyncSession,
        company_name: str,
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get upcoming tenders that might interest a specific company."""
        # Calculate date range (next 30 days)
        today = date.today()
        thirty_days_from_now = today + timedelta(days=30)
        
        # Build query for upcoming tenders
        query = select(Tender).where(
            and_(
                Tender.deadline_date >= today,
                Tender.deadline_date <= thirty_days_from_now
            )
        )
        
        # Add filters
        if cpv_codes:
            cpv_conditions = []
            for cpv in cpv_codes:
                cpv_conditions.append(Tender.cpv_codes.contains([cpv]))
            query = query.where(or_(*cpv_conditions))
        
        if country:
            query = query.where(Tender.buyer_country == country.upper())
        
        # Execute query
        result = await db.execute(query.order_by(Tender.deadline_date).limit(limit))
        tenders = result.scalars().all()
        
        # Convert to dict format
        upcoming_tenders = []
        for tender in tenders:
            upcoming_tenders.append({
                "title": tender.title,
                "deadline": tender.deadline_date,
                "country": tender.buyer_country,
                "value": tender.value_amount,
                "currency": tender.currency,
                "url": tender.url,
                "cpv_codes": tender.cpv_codes
            })
        
        return upcoming_tenders


# Global service instance
outreach_targeting_service = OutreachTargetingService()
