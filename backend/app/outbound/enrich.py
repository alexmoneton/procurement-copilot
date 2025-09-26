"""
Hunter.io enrichment system for finding contact emails.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..db.models_outbound import Prospect, ContactCache, ContactSource, OutboundLog, OutboundEvent
from ..core.config import settings
from .utils import (
    normalize_company, is_cache_valid, get_cache_expiry, 
    is_role_email, extract_domain_from_email, validate_email_format
)

logger = logging.getLogger(__name__)


class HunterEnrichment:
    """Hunter.io enrichment system."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.api_key = settings.hunter_api_key
        self.daily_cap = settings.hunter_daily_cap
        self.base_url = "https://api.hunter.io/v2"
        self._daily_usage = 0
        self._last_reset_date = datetime.utcnow().date()
    
    async def enrich_prospect(self, prospect: Prospect) -> Optional[str]:
        """
        Enrich prospect with contact information.
        
        Args:
            prospect: Prospect to enrich
            
        Returns:
            Best email found or None
        """
        try:
            # Check cache first
            cached_email = await self._get_cached_email(prospect.normalized_company)
            if cached_email:
                self.logger.info(f"Using cached email for {prospect.normalized_company}")
                return cached_email
            
            # Check daily cap
            if not await self._check_daily_cap():
                self.logger.warning("Daily Hunter.io cap reached")
                return None
            
            # Try domain search first
            domain = await self._find_domain(prospect.company_name)
            if domain:
                email = await self._domain_search(domain, prospect.company_name)
                if email:
                    await self._cache_contact(prospect.normalized_company, domain, email)
                    return email
            
            # Try email finder as fallback
            email = await self._email_finder(prospect.company_name)
            if email:
                domain = extract_domain_from_email(email)
                if domain:
                    await self._cache_contact(prospect.normalized_company, domain, email)
                return email
            
            # Mark as invalid if no email found
            prospect.status = "invalid"
            await self.db.commit()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error enriching prospect {prospect.id}: {e}")
            return None
    
    async def _get_cached_email(self, normalized_company: str) -> Optional[str]:
        """
        Get cached email for company.
        
        Args:
            normalized_company: Normalized company name
            
        Returns:
            Cached email or None
        """
        try:
            query = select(ContactCache).where(
                and_(
                    ContactCache.normalized_company == normalized_company,
                    ContactCache.expires_at > datetime.utcnow(),
                    ContactCache.confidence >= 0.7
                )
            ).order_by(ContactCache.confidence.desc())
            
            result = await self.db.execute(query)
            cached_contact = result.scalar_one_or_none()
            
            if cached_contact and is_cache_valid(cached_contact.expires_at):
                return cached_contact.email
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached email: {e}")
            return None
    
    async def _check_daily_cap(self) -> bool:
        """
        Check if daily API cap is reached.
        
        Returns:
            True if under cap, False if cap reached
        """
        try:
            # Reset daily usage if new day
            current_date = datetime.utcnow().date()
            if current_date > self._last_reset_date:
                self._daily_usage = 0
                self._last_reset_date = current_date
            
            # Check against cap
            if self._daily_usage >= self.daily_cap:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking daily cap: {e}")
            return False
    
    async def _find_domain(self, company_name: str) -> Optional[str]:
        """
        Find company domain using Hunter.io domain search.
        
        Args:
            company_name: Company name
            
        Returns:
            Domain or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/domain-search",
                    params={
                        "api_key": self.api_key,
                        "company": company_name,
                        "limit": 1
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("domain"):
                        domain = data["data"]["domain"]
                        self.logger.info(f"Found domain {domain} for {company_name}")
                        return domain
                
                self.logger.warning(f"No domain found for {company_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error finding domain for {company_name}: {e}")
            return None
    
    async def _domain_search(self, domain: str, company_name: str) -> Optional[str]:
        """
        Search for emails in domain.
        
        Args:
            domain: Domain to search
            company_name: Company name for context
            
        Returns:
            Best email found or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/domain-search",
                    params={
                        "api_key": self.api_key,
                        "domain": domain,
                        "limit": 10
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    emails = data.get("data", {}).get("emails", [])
                    
                    # Find best email
                    best_email = self._select_best_email(emails, company_name)
                    if best_email:
                        self._daily_usage += 1
                        self.logger.info(f"Found email {best_email} for {company_name}")
                        return best_email
                
                self.logger.warning(f"No emails found for domain {domain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in domain search for {domain}: {e}")
            return None
    
    async def _email_finder(self, company_name: str) -> Optional[str]:
        """
        Use email finder to find contact.
        
        Args:
            company_name: Company name
            
        Returns:
            Best email found or None
        """
        try:
            # Extract first and last name from company name (heuristic)
            name_parts = company_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[1]
            else:
                first_name = name_parts[0] if name_parts else "info"
                last_name = "contact"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/email-finder",
                    params={
                        "api_key": self.api_key,
                        "domain": f"{normalize_company(company_name)}.com",  # Heuristic
                        "first_name": first_name,
                        "last_name": last_name
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    email = data.get("data", {}).get("email")
                    if email and validate_email_format(email) and not is_role_email(email):
                        self._daily_usage += 1
                        self.logger.info(f"Found email {email} for {company_name}")
                        return email
                
                self.logger.warning(f"No email found for {company_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in email finder for {company_name}: {e}")
            return None
    
    def _select_best_email(self, emails: List[Dict], company_name: str) -> Optional[str]:
        """
        Select best email from list.
        
        Args:
            emails: List of email dictionaries
            company_name: Company name for context
            
        Returns:
            Best email or None
        """
        if not emails:
            return None
        
        # Score emails based on various factors
        scored_emails = []
        for email_data in emails:
            email = email_data.get("email", "")
            confidence = email_data.get("confidence", 0)
            
            if not email or not validate_email_format(email):
                continue
            
            if is_role_email(email):
                continue
            
            # Calculate score
            score = confidence
            
            # Boost score for certain patterns
            email_lower = email.lower()
            if any(pattern in email_lower for pattern in ["ceo", "founder", "director", "manager"]):
                score += 0.2
            
            if any(pattern in email_lower for pattern in ["procurement", "tender", "business"]):
                score += 0.1
            
            scored_emails.append((email, score))
        
        if not scored_emails:
            return None
        
        # Return highest scoring email
        best_email = max(scored_emails, key=lambda x: x[1])
        return best_email[0]
    
    async def _cache_contact(
        self, 
        normalized_company: str, 
        domain: str, 
        email: str, 
        confidence: float = 0.8
    ):
        """
        Cache contact information.
        
        Args:
            normalized_company: Normalized company name
            domain: Domain
            email: Email address
            confidence: Confidence score
        """
        try:
            # Check if already cached
            existing_query = select(ContactCache).where(ContactCache.email == email)
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing cache
                existing.normalized_company = normalized_company
                existing.domain = domain
                existing.confidence = confidence
                existing.discovered_at = datetime.utcnow()
                existing.expires_at = get_cache_expiry()
            else:
                # Create new cache entry
                new_cache = ContactCache(
                    normalized_company=normalized_company,
                    domain=domain,
                    email=email,
                    source=ContactSource.HUNTER,
                    confidence=confidence,
                    expires_at=get_cache_expiry()
                )
                self.db.add(new_cache)
            
            await self.db.commit()
            self.logger.info(f"Cached contact {email} for {normalized_company}")
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error caching contact: {e}")
    
    async def enrich_prospects(
        self, 
        prospects: List[Prospect], 
        max_enrichments: int = 50
    ) -> Dict[str, int]:
        """
        Enrich multiple prospects.
        
        Args:
            prospects: List of prospects to enrich
            max_enrichments: Maximum number of enrichments to perform
            
        Returns:
            Dictionary with enrichment statistics
        """
        enriched_count = 0
        error_count = 0
        
        try:
            for prospect in prospects:
                if enriched_count >= max_enrichments:
                    break
                
                if prospect.status in ["enriched", "sent", "bounced", "unsub", "suppressed", "invalid"]:
                    continue
                
                email = await self.enrich_prospect(prospect)
                if email:
                    prospect.status = "enriched"
                    enriched_count += 1
                    
                    # Log enrichment
                    log_entry = OutboundLog(
                        prospect_id=prospect.id,
                        email=email,
                        campaign="enrichment",
                        event=OutboundEvent.QUEUED,
                        meta={"source": "hunter", "confidence": 0.8}
                    )
                    self.db.add(log_entry)
                else:
                    error_count += 1
                
                # Rate limiting
                await asyncio.sleep(1)  # 1 second between requests
            
            await self.db.commit()
            
            return {
                "prospects_processed": len(prospects),
                "enriched": enriched_count,
                "errors": error_count,
                "daily_usage": self._daily_usage
            }
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error in batch enrichment: {e}")
            return {
                "prospects_processed": len(prospects),
                "enriched": 0,
                "errors": len(prospects),
                "error": str(e)
            }
