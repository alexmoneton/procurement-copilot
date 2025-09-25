"""BOAMP France scraper."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger
from selectolax.parser import HTMLParser

from ..core.config import settings
from .common import BaseScraper, ScrapingError


class BOAMPFRScraper(BaseScraper):
    """Scraper for BOAMP France (Bulletin Officiel des Annonces de Marchés Publics)."""

    def __init__(self):
        super().__init__("BOAMP_FR")
        self.base_url = "https://www.boamp.fr"
        self.search_url = f"{self.base_url}/avis"

    async def fetch_tenders(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch tenders from BOAMP France."""
        self.logger.info(f"Fetching {limit} tenders from BOAMP France")

        try:
            tenders = []
            page = 1

            while len(tenders) < limit:
                # Fetch search results page
                search_params = {
                    "page": page,
                    "per_page": min(50, limit - len(tenders)),
                    "sort": "date_publication",
                    "order": "desc",
                }

                response = await self._make_request(
                    self.search_url, params=search_params
                )
                page_tenders = self._parse_search_page(response.text)

                if not page_tenders:
                    self.logger.info("No more tenders found, stopping pagination")
                    break

                # Fetch detailed information for each tender
                for tender_summary in page_tenders:
                    if len(tenders) >= limit:
                        break

                    try:
                        detailed_tender = await self._fetch_tender_details(
                            tender_summary
                        )
                        if detailed_tender:
                            tenders.append(detailed_tender)
                    except Exception as e:
                        self.logger.warning(f"Error fetching tender details: {e}")
                        continue

                page += 1

                # Safety check to prevent infinite loops
                if page > 20:  # Max 20 pages
                    self.logger.warning("Reached maximum page limit, stopping")
                    break

            self.logger.info(
                f"Successfully fetched {len(tenders)} tenders from BOAMP France"
            )
            return tenders

        except Exception as e:
            self.logger.error(f"Error fetching BOAMP tenders: {e}")
            raise ScrapingError(f"Failed to fetch BOAMP tenders: {e}")

    def _parse_search_page(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse search results page to extract tender summaries."""
        tenders = []

        try:
            parser = HTMLParser(html_content)

            # Find tender result items (this selector may need adjustment based on actual HTML)
            tender_items = parser.css("article.avis, .tender-item, .result-item")

            for item in tender_items:
                try:
                    # Extract basic information from search result
                    title_elem = item.css_first("h2 a, h3 a, .title a, .tender-title a")
                    if not title_elem:
                        continue

                    title = self._clean_text(title_elem.text())
                    link = title_elem.attributes.get("href", "")

                    if not title or not link:
                        continue

                    # Make URL absolute
                    url = urljoin(self.base_url, link)

                    # Extract tender reference from URL or text
                    tender_ref = self._extract_tender_ref(url, item)

                    # Extract publication date
                    date_elem = item.css_first(
                        ".date, .publication-date, .date-publication"
                    )
                    publication_date = None
                    if date_elem:
                        publication_date = self._parse_date(date_elem.text())

                    # Extract buyer information
                    buyer_elem = item.css_first(".buyer, .organisme, .publisher")
                    buyer_name = (
                        self._clean_text(buyer_elem.text()) if buyer_elem else None
                    )

                    # Extract value if available
                    value_elem = item.css_first(".value, .montant, .amount")
                    value_amount = None
                    if value_elem:
                        value_amount = self._parse_decimal(value_elem.text())

                    tenders.append(
                        {
                            "tender_ref": tender_ref,
                            "title": title,
                            "url": url,
                            "publication_date": publication_date,
                            "buyer_name": buyer_name,
                            "value_amount": value_amount,
                        }
                    )

                except Exception as e:
                    self.logger.warning(f"Error parsing tender item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing search page: {e}")
            raise ScrapingError(f"Failed to parse search page: {e}")

        return tenders

    async def _fetch_tender_details(
        self, tender_summary: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific tender."""
        try:
            response = await self._make_request(tender_summary["url"])
            return self._parse_tender_details(response.text, tender_summary)

        except Exception as e:
            self.logger.warning(f"Error fetching tender details: {e}")
            return None

    def _parse_tender_details(
        self, html_content: str, summary: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Parse detailed tender page."""
        try:
            parser = HTMLParser(html_content)

            # Extract summary/description
            summary_elem = parser.css_first(".summary, .description, .objet, .content")
            summary_text = (
                self._clean_text(summary_elem.text()) if summary_elem else None
            )

            # Extract deadline date
            deadline_elem = parser.css_first(".deadline, .date-limite, .closing-date")
            deadline_date = None
            if deadline_elem:
                deadline_date = self._parse_date(deadline_elem.text())

            # Extract CPV codes
            cpv_codes = self._extract_cpv_codes_from_html(parser)

            # Extract buyer country (default to France for BOAMP)
            buyer_country = "FR"

            # Extract currency (default to EUR for France)
            currency = "EUR"

            # Extract value if not already available
            value_amount = summary.get("value_amount")
            if not value_amount:
                value_elem = parser.css_first(".value, .montant, .amount, .estimation")
                if value_elem:
                    value_amount = self._parse_decimal(value_elem.text())

            return {
                "tender_ref": summary["tender_ref"],
                "source": "BOAMP_FR",
                "title": summary["title"],
                "summary": summary_text,
                "publication_date": summary.get("publication_date"),
                "deadline_date": deadline_date,
                "cpv_codes": cpv_codes,
                "buyer_name": summary.get("buyer_name"),
                "buyer_country": buyer_country,
                "value_amount": value_amount,
                "currency": currency,
                "url": summary["url"],
            }

        except Exception as e:
            self.logger.warning(f"Error parsing tender details: {e}")
            return None

    def _extract_tender_ref(self, url: str, item_element: Any) -> str:
        """Extract tender reference from URL or page element."""
        # Try to extract from URL
        url_match = re.search(r"/(\d+)/", url)
        if url_match:
            return f"BOAMP_{url_match.group(1)}"

        # Try to extract from page element
        ref_elem = item_element.css_first(".ref, .reference, .numero, .number")
        if ref_elem:
            ref_text = self._clean_text(ref_elem.text())
            if ref_text:
                return f"BOAMP_{ref_text}"

        # Fallback: use URL hash
        return f"BOAMP_{hash(url) % 1000000:06d}"

    def _extract_cpv_codes_from_html(self, parser: HTMLParser) -> List[str]:
        """Extract CPV codes from HTML content."""
        cpv_codes = []

        # Look for CPV codes in various formats
        cpv_selectors = [
            ".cpv, .cpv-code, .cpv-codes",
            "[class*='cpv']",
            "td:contains('CPV')",
            "span:contains('CPV')",
        ]

        for selector in cpv_selectors:
            try:
                elements = parser.css(selector)
                for elem in elements:
                    try:
                        text = self._clean_text(elem.text())
                        if text:
                            # Extract 8-digit codes
                            codes = re.findall(r"\b\d{8}\b", text)
                            cpv_codes.extend(codes)
                    except Exception as e:
                        self.logger.warning(f"Error processing element: {e}")
                        continue
            except Exception as e:
                self.logger.warning(f"Error with selector {selector}: {e}")
                continue

        return self._normalize_cpv_codes(cpv_codes)


# Convenience function for external use
async def fetch_last_tenders_boamp(limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch last tenders from BOAMP France."""
    async with BOAMPFRScraper() as scraper:
        return await scraper.fetch_tenders(limit)
