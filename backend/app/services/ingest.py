"""ETL service for ingesting tender data."""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.crud import TenderCRUD
from ..db.schemas import TenderCreate
from ..scrapers.ted import fetch_last_tenders
from ..scrapers.boamp_fr import fetch_last_tenders_boamp
from ..scrapers.real_data import fetch_real_ted_tenders, fetch_real_boamp_tenders
from ..scrapers.european_platforms import fetch_all_european_tenders
from .cpv import cpv_mapper
from .dedupe import deduplicator


class IngestService:
    """Service for ingesting tender data from various sources."""
    
    def __init__(self):
        self.logger = logger.bind(service="ingest")
    
    async def run_ingest(
        self, 
        db: AsyncSession, 
        ted_limit: int = 200, 
        boamp_limit: int = 200
    ) -> Dict[str, int]:
        """Run the complete ingestion pipeline (legacy method)."""
        return await self.run_full_european_ingest(db, ted_limit, boamp_limit, 0)
    
    async def run_full_european_ingest(
        self, 
        db: AsyncSession, 
        ted_limit: int = 50, 
        boamp_limit: int = 30,
        european_limit_per_country: int = 15
    ) -> Dict[str, int]:
        """Run the complete European ingestion pipeline."""
        self.logger.info("Starting full European tender ingestion pipeline")
        
        # Fetch data from all sources
        all_tenders = []
        
        # Fetch from TED (using real data scraper)
        try:
            self.logger.info(f"Fetching {ted_limit} real tenders from TED")
            ted_tenders = await fetch_real_ted_tenders(ted_limit)
            all_tenders.extend(ted_tenders)
            self.logger.info(f"Fetched {len(ted_tenders)} real tenders from TED")
        except Exception as e:
            self.logger.error(f"Error fetching real TED tenders: {e}")
            # Fallback to original scraper
            try:
                self.logger.info("Falling back to original TED scraper")
                ted_tenders = await fetch_last_tenders(ted_limit)
                all_tenders.extend(ted_tenders)
            except Exception as fallback_e:
                self.logger.error(f"Fallback TED scraper also failed: {fallback_e}")
        
        # Fetch from BOAMP (using real data scraper)
        try:
            self.logger.info(f"Fetching {boamp_limit} real tenders from BOAMP")
            boamp_tenders = await fetch_real_boamp_tenders(boamp_limit)
            all_tenders.extend(boamp_tenders)
            self.logger.info(f"Fetched {len(boamp_tenders)} real tenders from BOAMP")
        except Exception as e:
            self.logger.error(f"Error fetching real BOAMP tenders: {e}")
            # Fallback to original scraper
            try:
                self.logger.info("Falling back to original BOAMP scraper")
                boamp_tenders = await fetch_last_tenders_boamp(boamp_limit)
                all_tenders.extend(boamp_tenders)
            except Exception as fallback_e:
                self.logger.error(f"Fallback BOAMP scraper also failed: {fallback_e}")
        
        # Fetch from all European platforms (if enabled)
        if european_limit_per_country > 0:
            try:
                self.logger.info(f"Fetching tenders from all European platforms ({european_limit_per_country} per country)")
                european_tenders = await fetch_all_european_tenders(european_limit_per_country)
                all_tenders.extend(european_tenders)
                self.logger.info(f"Fetched {len(european_tenders)} tenders from European platforms")
            except Exception as e:
                self.logger.error(f"Error fetching European platform tenders: {e}")
        
        if not all_tenders:
            self.logger.warning("No tenders fetched from any source")
            return {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        # Process and normalize data
        self.logger.info(f"Processing {len(all_tenders)} raw tenders")
        processed_tenders = await self._process_tenders(all_tenders)
        
        # Deduplicate
        self.logger.info("Deduplicating tenders")
        deduplicated_tenders = deduplicator.deduplicate_tenders(processed_tenders)
        
        # Upsert to database
        self.logger.info(f"Upserting {len(deduplicated_tenders)} tenders to database")
        results = await self._upsert_tenders(db, deduplicated_tenders)
        
        self.logger.info(
            f"Ingestion completed: {results['inserted']} inserted, "
            f"{results['updated']} updated, {results['skipped']} skipped, "
            f"{results['errors']} errors"
        )
        
        return results
    
    async def _process_tenders(self, raw_tenders: List[Dict]) -> List[Dict]:
        """Process and normalize raw tender data."""
        processed = []
        
        for tender in raw_tenders:
            try:
                processed_tender = self._normalize_tender(tender)
                if processed_tender:
                    processed.append(processed_tender)
            except Exception as e:
                self.logger.warning(f"Error processing tender {tender.get('tender_ref', 'unknown')}: {e}")
                continue
        
        return processed
    
    def _normalize_tender(self, tender: Dict) -> Optional[Dict]:
        """Normalize a single tender record."""
        try:
            # Validate required fields
            if not tender.get("tender_ref") or not tender.get("title"):
                self.logger.warning(f"Tender missing required fields: {tender.get('tender_ref', 'unknown')}")
                return None
            
            # Normalize CPV codes
            cpv_codes = tender.get("cpv_codes", [])
            if not cpv_codes and tender.get("title"):
                # Try to suggest CPV codes based on title and summary
                suggested_codes = cpv_mapper.suggest_cpv_codes(
                    tender.get("title", ""),
                    tender.get("summary", "")
                )
                cpv_codes = suggested_codes[:5]  # Limit to 5 suggestions
            
            normalized_cpv = cpv_mapper.validate_cpv_codes(cpv_codes)
            
            # Normalize country code
            country = tender.get("buyer_country", "")
            if country:
                country = country.upper()[:2]  # Take first 2 characters and uppercase
            
            # Normalize currency
            currency = tender.get("currency", "")
            if currency:
                currency = currency.upper()[:3]  # Take first 3 characters and uppercase
            
            # Clean and validate text fields
            title = self._clean_text(tender.get("title", ""))
            summary = self._clean_text(tender.get("summary", ""))
            buyer_name = self._clean_text(tender.get("buyer_name", ""))
            url = self._clean_text(tender.get("url", ""))
            
            if not title:
                return None
            
            return {
                "tender_ref": tender["tender_ref"],
                "source": tender.get("source", "UNKNOWN"),
                "title": title,
                "summary": summary if summary else None,
                "publication_date": tender.get("publication_date"),
                "deadline_date": tender.get("deadline_date"),
                "cpv_codes": normalized_cpv,
                "buyer_name": buyer_name if buyer_name else None,
                "buyer_country": country or "XX",
                "value_amount": tender.get("value_amount"),
                "currency": currency if currency else None,
                "url": url if url else f"https://example.com/tender/{tender['tender_ref']}",
            }
            
        except Exception as e:
            self.logger.error(f"Error normalizing tender: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.strip().split())
        
        # Remove HTML entities
        html_entities = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&nbsp;": " ",
        }
        
        for entity, replacement in html_entities.items():
            cleaned = cleaned.replace(entity, replacement)
        
        return cleaned.strip()
    
    async def _upsert_tenders(self, db: AsyncSession, tenders: List[Dict]) -> Dict[str, int]:
        """Upsert tenders to database."""
        results = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        for tender in tenders:
            try:
                # Check if tender already exists
                existing = await TenderCRUD.get_by_ref(db, tender["tender_ref"])
                
                if existing:
                    # Update existing tender
                    from ..db.schemas import TenderUpdate
                    update_data = TenderUpdate(**{k: v for k, v in tender.items() if k != "tender_ref"})
                    updated = await TenderCRUD.update(db, existing.id, update_data)
                    
                    if updated:
                        results["updated"] += 1
                        self.logger.debug(f"Updated tender: {tender['tender_ref']}")
                    else:
                        results["skipped"] += 1
                        self.logger.debug(f"Skipped tender (update failed): {tender['tender_ref']}")
                else:
                    # Create new tender
                    tender_create = TenderCreate(**tender)
                    created = await TenderCRUD.create(db, tender_create)
                    
                    if created:
                        results["inserted"] += 1
                        self.logger.debug(f"Inserted tender: {tender['tender_ref']}")
                    else:
                        results["skipped"] += 1
                        self.logger.debug(f"Skipped tender (creation failed): {tender['tender_ref']}")
                
            except Exception as e:
                results["errors"] += 1
                self.logger.error(f"Error upserting tender {tender.get('tender_ref', 'unknown')}: {e}")
                continue
        
        return results
    
    async def ingest_single_source(
        self, 
        db: AsyncSession, 
        source: str, 
        limit: int = 200
    ) -> Dict[str, int]:
        """Ingest tenders from a single source."""
        self.logger.info(f"Starting ingestion from {source}")
        
        # Fetch data from specified source
        if source.upper() == "TED":
            raw_tenders = await fetch_last_tenders(limit)
        elif source.upper() == "BOAMP_FR":
            raw_tenders = await fetch_last_tenders_boamp(limit)
        else:
            raise ValueError(f"Unknown source: {source}")
        
        if not raw_tenders:
            self.logger.warning(f"No tenders fetched from {source}")
            return {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        # Process and normalize data
        processed_tenders = await self._process_tenders(raw_tenders)
        
        # Deduplicate
        deduplicated_tenders = deduplicator.deduplicate_tenders(processed_tenders)
        
        # Upsert to database
        results = await self._upsert_tenders(db, deduplicated_tenders)
        
        self.logger.info(
            f"Ingestion from {source} completed: {results['inserted']} inserted, "
            f"{results['updated']} updated, {results['skipped']} skipped, "
            f"{results['errors']} errors"
        )
        
        return results


# Global instance
ingest_service = IngestService()
