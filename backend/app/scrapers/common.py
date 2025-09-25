"""Common utilities for scrapers."""

import asyncio
import random
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from ..core.config import settings


class ScrapingError(Exception):
    """Base exception for scraping errors."""

    pass


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""

    pass


class ScrapingTimeoutError(ScrapingError):
    """Exception raised when scraping times out."""

    pass


class BaseScraper:
    """Base class for all scrapers."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(scraper=name)
        self.client = httpx.AsyncClient(
            timeout=settings.scraping.request_timeout,
            headers={"User-Agent": settings.scraping.user_agent},
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request with retries and rate limiting."""
        # Add jitter to avoid thundering herd
        await asyncio.sleep(random.uniform(0.1, settings.scraping.rate_limit_delay))

        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            self.logger.debug(f"Request successful: {url}")
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.logger.warning(f"Rate limited: {url}")
                raise RateLimitError(f"Rate limited: {e.response.status_code}")
            elif e.response.status_code >= 500:
                self.logger.warning(f"Server error: {url} - {e.response.status_code}")
                raise
            else:
                self.logger.error(f"HTTP error: {url} - {e.response.status_code}")
                raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {url} - {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {url} - {e}")
            raise ScrapingError(f"Unexpected error: {e}")

    def _parse_date(self, date_str: str, formats: List[str] = None) -> Optional[date]:
        """Parse date string with multiple format support."""
        if not date_str or date_str.strip() == "":
            return None

        if formats is None:
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ]

        for fmt in formats:
            try:
                if "T" in fmt:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.date()
                else:
                    return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        self.logger.warning(f"Could not parse date: {date_str}")
        return None

    def _parse_decimal(self, value_str: str) -> Optional[Decimal]:
        """Parse decimal value from string."""
        if not value_str or value_str.strip() == "":
            return None

        try:
            # Remove common currency symbols and whitespace
            cleaned = (
                value_str.strip().replace("€", "").replace("$", "").replace(",", "")
            )
            return Decimal(cleaned)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse decimal: {value_str}")
            return None

    def _normalize_cpv_codes(self, cpv_codes: List[str]) -> List[str]:
        """Normalize CPV codes to standard format."""
        normalized = []
        for code in cpv_codes:
            if not code or not code.strip():
                continue

            # Remove dots and spaces, keep only digits
            cleaned = "".join(c for c in code.strip() if c.isdigit())

            # CPV codes should be 8 digits
            if len(cleaned) == 8:
                normalized.append(cleaned)
            elif len(cleaned) > 8:
                # Take first 8 digits
                normalized.append(cleaned[:8])
            else:
                # Pad with zeros
                normalized.append(cleaned.ljust(8, "0"))

        return list(set(normalized))  # Remove duplicates

    def _normalize_country_code(self, country: str) -> str:
        """Normalize country code to ISO 3166-1 alpha-2 format."""
        if not country:
            return "XX"

        country = country.strip().upper()

        # Common country mappings
        country_mappings = {
            "FRANCE": "FR",
            "FR": "FR",
            "UNITED KINGDOM": "GB",
            "UK": "GB",
            "GB": "GB",
            "GERMANY": "DE",
            "DE": "DE",
            "SPAIN": "ES",
            "ES": "ES",
            "ITALY": "IT",
            "IT": "IT",
            "NETHERLANDS": "NL",
            "NL": "NL",
            "BELGIUM": "BE",
            "BE": "BE",
            "LUXEMBOURG": "LU",
            "LU": "LU",
            "AUSTRIA": "AT",
            "AT": "AT",
            "PORTUGAL": "PT",
            "PT": "PT",
            "IRELAND": "IE",
            "IE": "IE",
            "FINLAND": "FI",
            "FI": "FI",
            "SWEDEN": "SE",
            "SE": "SE",
            "DENMARK": "DK",
            "DK": "DK",
            "NORWAY": "NO",
            "NO": "NO",
            "POLAND": "PL",
            "PL": "PL",
            "CZECH REPUBLIC": "CZ",
            "CZ": "CZ",
            "HUNGARY": "HU",
            "HU": "HU",
            "SLOVAKIA": "SK",
            "SK": "SK",
            "SLOVENIA": "SI",
            "SI": "SI",
            "CROATIA": "HR",
            "HR": "HR",
            "ROMANIA": "RO",
            "RO": "RO",
            "BULGARIA": "BG",
            "BG": "BG",
            "GREECE": "GR",
            "GR": "GR",
            "CYPRUS": "CY",
            "CY": "CY",
            "MALTA": "MT",
            "MT": "MT",
            "ESTONIA": "EE",
            "EE": "EE",
            "LATVIA": "LV",
            "LV": "LV",
            "LITHUANIA": "LT",
            "LT": "LT",
        }

        return country_mappings.get(country, country[:2] if len(country) >= 2 else "XX")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove extra whitespace and normalize
        cleaned = " ".join(text.strip().split())

        # Remove common HTML entities
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

    async def fetch_tenders(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch tenders from the source. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement fetch_tenders method")
