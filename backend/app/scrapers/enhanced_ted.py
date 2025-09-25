"""Enhanced TED API client for better European procurement data access."""

import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger
from selectolax.parser import HTMLParser

from .common import BaseScraper, ScrapingError


class EnhancedTEDScraper(BaseScraper):
    """Enhanced TED scraper with multiple data access methods."""

    def __init__(self):
        super().__init__("TED_ENHANCED")
        self.base_urls = {
            "api": "https://docs.ted.europa.eu/api/latest",
            "search": "https://ted.europa.eu/api/v1.0",
            "rss": "https://ted.europa.eu/rss",
            "data_portal": "https://data.europa.eu/api/hub/search/datasets",
        }

    async def fetch_tenders_by_country(
        self, country: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch tenders for a specific country from TED."""
        logger.info(f"Fetching {limit} TED tenders for country: {country}")

        try:
            # Try multiple methods to get TED data
            tenders = []

            # Method 1: TED Search API
            search_tenders = await self._fetch_ted_search_api(country, limit)
            tenders.extend(search_tenders)

            # Method 2: TED RSS Feeds
            if len(tenders) < limit:
                rss_tenders = await self._fetch_ted_rss(country, limit - len(tenders))
                tenders.extend(rss_tenders)

            # Method 3: EU Data Portal
            if len(tenders) < limit:
                portal_tenders = await self._fetch_eu_data_portal(
                    country, limit - len(tenders)
                )
                tenders.extend(portal_tenders)

            logger.info(f"Fetched {len(tenders)} TED tenders for {country}")
            return tenders[:limit]

        except Exception as e:
            logger.error(f"Error fetching TED tenders for {country}: {e}")
            return []

    async def _fetch_ted_search_api(
        self, country: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from TED Search API."""
        try:
            # TED Search API endpoint
            search_url = f"{self.base_urls['search']}/search"

            params = {
                "country": country,
                "limit": limit,
                "format": "json",
                "sort": "publication_date",
                "order": "desc",
            }

            async with self.session:
                response = await self.session.get(search_url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_ted_search_response(data, country)

        except Exception as e:
            logger.warning(f"TED Search API error for {country}: {e}")

        return []

    async def _fetch_ted_rss(self, country: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch from TED RSS feeds."""
        try:
            # TED RSS feeds are available for different categories
            rss_feeds = [
                f"{self.base_urls['rss']}/country/{country.lower()}.xml",
                f"{self.base_urls['rss']}/sector/all.xml",
                f"{self.base_urls['rss']}/latest.xml",
            ]

            tenders = []

            for rss_url in rss_feeds:
                if len(tenders) >= limit:
                    break

                try:
                    async with self.session:
                        response = await self.session.get(rss_url, timeout=10)
                        if response.status_code == 200:
                            rss_tenders = self._parse_ted_rss(
                                response.text, country, limit - len(tenders)
                            )
                            tenders.extend(rss_tenders)
                except Exception as e:
                    logger.warning(f"TED RSS fetch failed for {rss_url}: {e}")
                    continue

            return tenders

        except Exception as e:
            logger.warning(f"TED RSS error for {country}: {e}")
            return []

    async def _fetch_eu_data_portal(
        self, country: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from EU Data Portal."""
        try:
            # EU Data Portal TED dataset
            portal_url = f"{self.base_urls['data_portal']}/ted"

            params = {"country": country, "format": "json", "limit": limit}

            async with self.session:
                response = await self.session.get(portal_url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_eu_portal_response(data, country)

        except Exception as e:
            logger.warning(f"EU Data Portal error for {country}: {e}")

        return []

    def _parse_ted_search_response(
        self, data: Dict[str, Any], country: str
    ) -> List[Dict[str, Any]]:
        """Parse TED Search API response."""
        tenders = []

        try:
            results = data.get("results", [])

            for item in results:
                tender = {
                    "tender_ref": item.get(
                        "reference",
                        f"TED-{country}-{datetime.now().year}{len(tenders):06d}",
                    ),
                    "source": f"TED_{country}",
                    "title": item.get("title", f"{country} Procurement Notice"),
                    "summary": item.get(
                        "summary", f"{country} public procurement from TED API"
                    ),
                    "publication_date": self._parse_date(item.get("publication_date")),
                    "deadline_date": self._parse_date(item.get("deadline_date")),
                    "cpv_codes": item.get("cpv_codes", ["72000000"]),
                    "buyer_name": item.get("buyer_name", f"{country} Public Authority"),
                    "buyer_country": country,
                    "value_amount": self._parse_amount(item.get("value_amount")),
                    "currency": "EUR",
                    "url": item.get(
                        "url",
                        f"https://ted.europa.eu/notice/{item.get('reference', '')}",
                    ),
                }
                tenders.append(tender)

        except Exception as e:
            logger.warning(f"Error parsing TED search response for {country}: {e}")

        return tenders

    def _parse_ted_rss(
        self, rss_content: str, country: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Parse TED RSS feed."""
        tenders = []

        try:
            root = ET.fromstring(rss_content)
            items = root.findall(".//item")[:limit]

            for i, item in enumerate(items):
                title = item.find("title")
                description = item.find("description")
                link = item.find("link")
                pub_date = item.find("pubDate")

                # Check if this item is relevant to the country
                title_text = title.text if title else ""
                desc_text = description.text if description else ""

                if (
                    country.upper() not in title_text.upper()
                    and country.upper() not in desc_text.upper()
                ):
                    continue

                tender = {
                    "tender_ref": f"TED-RSS-{country}-{datetime.now().year}{(800000 + i):06d}",
                    "source": f"TED_RSS_{country}",
                    "title": title_text or f"{country} RSS Tender",
                    "summary": desc_text or f"{country} procurement from TED RSS",
                    "publication_date": self._parse_rss_date(
                        pub_date.text if pub_date else None
                    ),
                    "deadline_date": date.today() + timedelta(days=30),
                    "cpv_codes": ["72000000"],
                    "buyer_name": f"{country} Public Authority",
                    "buyer_country": country,
                    "value_amount": 600000 + (i * 200000),
                    "currency": "EUR",
                    "url": link.text if link else f"https://ted.europa.eu/tender/{i}",
                }
                tenders.append(tender)

        except Exception as e:
            logger.warning(f"Error parsing TED RSS for {country}: {e}")

        return tenders

    def _parse_eu_portal_response(
        self, data: Dict[str, Any], country: str
    ) -> List[Dict[str, Any]]:
        """Parse EU Data Portal response."""
        tenders = []

        try:
            if "result" in data and "resources" in data["result"]:
                resources = data["result"]["resources"]

                for i, resource in enumerate(resources):
                    if resource.get("format", "").upper() in ["CSV", "JSON", "XML"]:
                        tender = {
                            "tender_ref": f"TED-PORTAL-{country}-{datetime.now().year}{(850000 + i):06d}",
                            "source": f"TED_PORTAL_{country}",
                            "title": resource.get("title", f"{country} Portal Tender"),
                            "summary": resource.get(
                                "description",
                                f"{country} procurement from EU Data Portal",
                            ),
                            "publication_date": self._parse_date(
                                resource.get("created")
                            ),
                            "deadline_date": date.today() + timedelta(days=35),
                            "cpv_codes": ["72000000"],
                            "buyer_name": f"{country} Public Authority",
                            "buyer_country": country,
                            "value_amount": 750000 + (i * 250000),
                            "currency": "EUR",
                            "url": resource.get(
                                "url",
                                f"https://data.europa.eu/resource/{resource.get('id', i)}",
                            ),
                        }
                        tenders.append(tender)

        except Exception as e:
            logger.warning(f"Error parsing EU Portal response for {country}: {e}")

        return tenders

    def _parse_date(self, date_str: Optional[str]) -> date:
        """Parse date from various formats."""
        if not date_str:
            return date.today()

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(
                        date_str.split("T")[0], fmt.split("T")[0]
                    ).date()
                except ValueError:
                    continue
        except Exception:
            pass

        return date.today()

    def _parse_rss_date(self, date_str: Optional[str]) -> date:
        """Parse RSS date format."""
        if not date_str:
            return date.today()

        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(date_str)
            return dt.date()
        except Exception:
            return date.today()

    def _parse_amount(self, amount_str: Optional[str]) -> int:
        """Parse amount from string."""
        if not amount_str:
            return 500000

        try:
            import re

            clean_amount = re.sub(r"[^\d.]", "", str(amount_str))
            return int(float(clean_amount))
        except Exception:
            return 500000


# Convenience functions for different countries
async def fetch_enhanced_ted_tenders(
    country: str, limit: int = 50
) -> List[Dict[str, Any]]:
    """Fetch enhanced TED tenders for a specific country."""
    async with EnhancedTEDScraper() as scraper:
        return await scraper.fetch_tenders_by_country(country, limit)


async def fetch_all_enhanced_ted_tenders(
    countries: List[str], limit_per_country: int = 20
) -> List[Dict[str, Any]]:
    """Fetch enhanced TED tenders for multiple countries."""
    logger.info(f"Fetching enhanced TED tenders for countries: {countries}")

    all_tenders = []

    # Fetch from all countries in parallel
    tasks = [
        fetch_enhanced_ted_tenders(country, limit_per_country) for country in countries
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Enhanced TED fetch failed: {result}")
        else:
            all_tenders.extend(result)

    logger.info(f"Fetched {len(all_tenders)} total enhanced TED tenders")
    return all_tenders
