"""TED (Tenders Electronic Daily) scraper."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from loguru import logger

from .common import BaseScraper, ScrapingError
from ..core.config import settings


class TEDScraper(BaseScraper):
    """Scraper for TED (Tenders Electronic Daily) data."""
    
    def __init__(self):
        super().__init__("TED")
        self.base_url = "https://data.europa.eu/api/hub/search/datasets"
        self.dataset_id = "ted-csv"
    
    async def fetch_tenders(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch tenders from TED dataset."""
        self.logger.info(f"Fetching {limit} tenders from TED")
        
        try:
            # First, get the dataset metadata to find the CSV download URL
            dataset_url = f"{self.base_url}/{self.dataset_id}"
            response = await self._make_request(dataset_url)
            dataset_data = response.json()
            
            # Find the CSV download URL
            csv_url = self._find_csv_url(dataset_data)
            if not csv_url:
                raise ScrapingError("Could not find CSV download URL in TED dataset")
            
            self.logger.info(f"Downloading TED CSV from: {csv_url}")
            
            # Download and parse CSV
            csv_response = await self._make_request(csv_url)
            tenders = self._parse_csv(csv_response.text, limit)
            
            self.logger.info(f"Successfully parsed {len(tenders)} tenders from TED")
            return tenders
            
        except Exception as e:
            self.logger.error(f"Error fetching TED tenders: {e}")
            raise ScrapingError(f"Failed to fetch TED tenders: {e}")
    
    async def fetch_awarded_tenders(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch awarded tenders from TED with winner/loser information."""
        self.logger.info(f"Fetching {limit} awarded tenders from TED")
        
        try:
            # First, get the dataset metadata to find the CSV download URL
            dataset_url = f"{self.base_url}/{self.dataset_id}"
            response = await self._make_request(dataset_url)
            dataset_data = response.json()
            
            # Find the CSV download URL
            csv_url = self._find_csv_url(dataset_data)
            if not csv_url:
                raise ScrapingError("Could not find CSV download URL in TED dataset")
            
            self.logger.info(f"Downloading TED CSV from: {csv_url}")
            
            # Download and parse CSV
            csv_response = await self._make_request(csv_url)
            awards = self._parse_awarded_csv(csv_response.text, limit)
            
            self.logger.info(f"Successfully parsed {len(awards)} awarded tenders from TED")
            return awards
            
        except Exception as e:
            self.logger.error(f"Error fetching awarded tenders from TED: {e}")
            raise ScrapingError(f"Failed to fetch awarded tenders from TED: {e}")
    
    def _find_csv_url(self, dataset_data: Dict[str, Any]) -> Optional[str]:
        """Find CSV download URL in dataset metadata."""
        try:
            # Navigate through the dataset structure to find CSV resources
            if "result" in dataset_data:
                result = dataset_data["result"]
                if "resources" in result:
                    for resource in result["resources"]:
                        if resource.get("format", "").upper() == "CSV":
                            return resource.get("url")
            
            # Alternative structure
            if "resources" in dataset_data:
                for resource in dataset_data["resources"]:
                    if resource.get("format", "").upper() == "CSV":
                        return resource.get("url")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error parsing dataset metadata: {e}")
            return None
    
    def _parse_csv(self, csv_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse CSV content and extract tender data."""
        tenders = []
        
        try:
            # Use StringIO to read CSV content
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io)
            
            for row_num, row in enumerate(reader):
                if len(tenders) >= limit:
                    break
                
                try:
                    tender = self._parse_tender_row(row)
                    if tender:
                        tenders.append(tender)
                except Exception as e:
                    self.logger.warning(f"Error parsing row {row_num}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            raise ScrapingError(f"Failed to parse CSV: {e}")
        
        return tenders
    
    def _parse_tender_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row into tender data."""
        try:
            # Extract basic information
            tender_ref = self._clean_text(row.get("TED_CN", ""))
            if not tender_ref:
                return None
            
            title = self._clean_text(row.get("TITLE", ""))
            if not title:
                return None
            
            # Parse dates
            publication_date = self._parse_date(row.get("DATE_PUB", ""))
            if not publication_date:
                return None
            
            deadline_date = self._parse_date(row.get("DEADLINE", ""))
            
            # Extract CPV codes
            cpv_codes = self._extract_cpv_codes(row)
            
            # Extract buyer information
            buyer_name = self._clean_text(row.get("BUYER_NAME", ""))
            buyer_country = self._normalize_country_code(row.get("COUNTRY", ""))
            
            # Extract financial information
            value_amount = self._parse_decimal(row.get("VALUE", ""))
            currency = self._extract_currency(row.get("CURRENCY", ""))
            
            # Extract URL
            url = self._clean_text(row.get("URL", ""))
            if not url:
                # Construct URL from tender reference
                url = f"https://ted.europa.eu/udl?uri=TED:NOTICE:{tender_ref}:TEXT:EN:HTML"
            
            # Extract summary
            summary = self._clean_text(row.get("SUMMARY", ""))
            
            return {
                "tender_ref": tender_ref,
                "source": "TED",
                "title": title,
                "summary": summary if summary else None,
                "publication_date": publication_date,
                "deadline_date": deadline_date,
                "cpv_codes": cpv_codes,
                "buyer_name": buyer_name if buyer_name else None,
                "buyer_country": buyer_country,
                "value_amount": value_amount,
                "currency": currency,
                "url": url,
            }
            
        except Exception as e:
            self.logger.warning(f"Error parsing tender row: {e}")
            return None
    
    def _extract_cpv_codes(self, row: Dict[str, str]) -> List[str]:
        """Extract CPV codes from row data."""
        cpv_codes = []
        
        # Try different possible column names for CPV codes
        cpv_columns = ["CPV", "CPV_CODE", "CPV_CODES", "MAIN_CPV", "CPV_MAIN"]
        
        for col in cpv_columns:
            if col in row and row[col]:
                cpv_str = self._clean_text(row[col])
                if cpv_str:
                    # Split by common separators
                    codes = [code.strip() for code in cpv_str.replace(",", ";").split(";")]
                    cpv_codes.extend(codes)
        
        return self._normalize_cpv_codes(cpv_codes)
    
    def _extract_currency(self, currency_str: str) -> Optional[str]:
        """Extract currency code from string."""
        if not currency_str:
            return None
        
        currency = self._clean_text(currency_str).upper()
        
        # Common currency mappings
        currency_mappings = {
            "EURO": "EUR",
            "EUR": "EUR",
            "€": "EUR",
            "DOLLAR": "USD",
            "USD": "USD",
            "$": "USD",
            "POUND": "GBP",
            "GBP": "GBP",
            "£": "GBP",
        }
        
        return currency_mappings.get(currency, currency[:3] if len(currency) >= 3 else None)
    
    def _parse_awarded_csv(self, csv_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse awarded tenders from CSV content."""
        awards = []
        
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row in csv_reader:
                if len(awards) >= limit:
                    break
                
                # Only process awarded notices
                notice_type = self._clean_text(row.get("TYPE", "")).upper()
                if notice_type not in ["AWARD", "CONTRACT_AWARD", "AWARD_NOTICE"]:
                    continue
                
                award = self._parse_award_row(row)
                if award:
                    awards.append(award)
            
        except Exception as e:
            self.logger.error(f"Error parsing awarded CSV: {e}")
            raise ScrapingError(f"Failed to parse awarded CSV: {e}")
        
        return awards
    
    def _parse_award_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single award row from CSV."""
        try:
            # Extract basic information
            tender_ref = self._clean_text(row.get("TED_CN", ""))
            if not tender_ref:
                return None
            
            # Extract award date
            award_date = self._parse_date(row.get("AWARD_DATE", ""))
            if not award_date:
                return None
            
            # Extract winner and other bidders
            winner_names = self._parse_supplier_names(row.get("WINNER", ""))
            other_bidders = self._parse_supplier_names(row.get("OTHER_BIDDERS", ""))
            
            # Extract CPV codes
            cpv_codes = self._extract_cpv_codes(row)
            
            # Extract buyer information
            buyer_country = self._normalize_country_code(row.get("COUNTRY", ""))
            buyer_name = self._clean_text(row.get("CONTRACTING_AUTHORITY", ""))
            
            # Extract financial information
            value_amount = self._parse_decimal(row.get("VALUE", ""))
            currency = self._extract_currency(row.get("CURRENCY", ""))
            
            # Extract title
            title = self._clean_text(row.get("TITLE", ""))
            
            return {
                "tender_ref": tender_ref,
                "award_date": award_date,
                "winner_names": winner_names,
                "other_bidders": other_bidders if other_bidders else None,
                "cpv_codes": cpv_codes,
                "buyer_country": buyer_country,
                "buyer_name": buyer_name if buyer_name else None,
                "value_amount": value_amount,
                "currency": currency,
                "title": title,
            }
            
        except Exception as e:
            self.logger.warning(f"Error parsing award row: {e}")
            return None
    
    def _parse_supplier_names(self, supplier_text: str) -> List[str]:
        """Parse supplier names from TED text field."""
        if not supplier_text or not supplier_text.strip():
            return []
        
        # Clean the text first
        supplier_text = self._clean_text(supplier_text)
        
        # Common separators in TED data
        separators = [';', '|', '\n', '\r\n', ' and ', ' & ', ' / ']
        
        names = [supplier_text]
        for sep in separators:
            new_names = []
            for name in names:
                new_names.extend([n.strip() for n in name.split(sep) if n.strip()])
            names = new_names
        
        # Clean up names
        cleaned_names = []
        for name in names:
            # Remove common prefixes/suffixes
            name = name.replace('Company:', '').replace('Supplier:', '').replace('Winner:', '').strip()
            # Remove extra whitespace
            name = ' '.join(name.split())
            # Filter out very short names and common non-company text
            if (name and len(name) > 2 and 
                not name.lower().startswith(('the ', 'a ', 'an ')) and
                not name.lower() in ['n/a', 'none', 'not specified', 'tbd']):
                cleaned_names.append(name)
        
        return cleaned_names


# Convenience function for external use
async def fetch_last_tenders(limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch last tenders from TED."""
    async with TEDScraper() as scraper:
        return await scraper.fetch_tenders(limit)


async def fetch_awarded_tenders(limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch awarded tenders from TED."""
    async with TEDScraper() as scraper:
        return await scraper.fetch_awarded_tenders(limit)
