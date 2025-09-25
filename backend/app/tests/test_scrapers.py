"""Tests for scrapers."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.scrapers.boamp_fr import BOAMPFRScraper, fetch_last_tenders_boamp
from app.scrapers.common import RateLimitError, ScrapingError
from app.scrapers.ted import TEDScraper, fetch_last_tenders


class TestTEDScraper:
    """Test TED scraper functionality."""

    @pytest.mark.asyncio
    async def test_ted_scraper_init(self):
        """Test TED scraper initialization."""
        scraper = TEDScraper()
        assert scraper.name == "TED"
        assert scraper.base_url == "https://data.europa.eu/api/hub/search/datasets"
        assert scraper.dataset_id == "ted-csv"

    @pytest.mark.asyncio
    async def test_parse_csv(self, mock_csv_content):
        """Test CSV parsing functionality."""
        scraper = TEDScraper()
        tenders = scraper._parse_csv(mock_csv_content, limit=10)

        assert len(tenders) == 2
        assert tenders[0]["tender_ref"] == "TEST-001"
        assert tenders[0]["title"] == "Test Tender 1"
        assert tenders[0]["source"] == "TED"
        assert tenders[0]["buyer_country"] == "FR"
        assert tenders[0]["cpv_codes"] == ["48000000"]

    @pytest.mark.asyncio
    async def test_parse_tender_row(self):
        """Test individual tender row parsing."""
        scraper = TEDScraper()

        row = {
            "TED_CN": "TEST-001",
            "TITLE": "Test Tender",
            "DATE_PUB": "2024-01-15",
            "DEADLINE": "2024-02-15",
            "CPV": "48000000",
            "BUYER_NAME": "Test Org",
            "COUNTRY": "FR",
            "VALUE": "100000",
            "CURRENCY": "EUR",
            "URL": "https://example.com",
            "SUMMARY": "Test summary",
        }

        tender = scraper._parse_tender_row(row)

        assert tender is not None
        assert tender["tender_ref"] == "TEST-001"
        assert tender["title"] == "Test Tender"
        assert tender["source"] == "TED"
        assert tender["buyer_country"] == "FR"
        assert tender["cpv_codes"] == ["48000000"]

    @pytest.mark.asyncio
    async def test_parse_tender_row_missing_required_fields(self):
        """Test parsing with missing required fields."""
        scraper = TEDScraper()

        row = {
            "TED_CN": "",  # Missing tender reference
            "TITLE": "Test Tender",
            "DATE_PUB": "2024-01-15",
        }

        tender = scraper._parse_tender_row(row)
        assert tender is None

    @pytest.mark.asyncio
    async def test_extract_cpv_codes(self):
        """Test CPV code extraction."""
        scraper = TEDScraper()

        row = {
            "CPV": "48000000;72000000",
            "CPV_CODE": "48000001",
        }

        cpv_codes = scraper._extract_cpv_codes(row)
        assert len(cpv_codes) >= 2
        assert "48000000" in cpv_codes

    @pytest.mark.asyncio
    async def test_extract_currency(self):
        """Test currency extraction."""
        scraper = TEDScraper()

        assert scraper._extract_currency("EUR") == "EUR"
        assert scraper._extract_currency("euro") == "EUR"
        assert scraper._extract_currency("€") == "EUR"
        assert scraper._extract_currency("") is None

    @pytest.mark.asyncio
    async def test_fetch_tenders_success(self, mock_httpx_client, mock_csv_content):
        """Test successful tender fetching."""
        scraper = TEDScraper()

        # Mock the dataset metadata response
        mock_dataset_response = MagicMock()
        mock_dataset_response.json.return_value = {
            "result": {
                "resources": [{"format": "CSV", "url": "https://example.com/data.csv"}]
            }
        }

        # Mock the CSV download response
        mock_csv_response = MagicMock()
        mock_csv_response.text = mock_csv_content

        with patch.object(scraper, "_make_request") as mock_request:
            mock_request.side_effect = [mock_dataset_response, mock_csv_response]

            tenders = await scraper.fetch_tenders(limit=10)

            assert len(tenders) == 2
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_tenders_no_csv_url(self):
        """Test fetching when no CSV URL is found."""
        scraper = TEDScraper()

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"resources": []}}

        with patch.object(scraper, "_make_request", return_value=mock_response):
            with pytest.raises(ScrapingError, match="Could not find CSV download URL"):
                await scraper.fetch_tenders(limit=10)


class TestBOAMPFRScraper:
    """Test BOAMP France scraper functionality."""

    @pytest.mark.asyncio
    async def test_boamp_scraper_init(self):
        """Test BOAMP scraper initialization."""
        scraper = BOAMPFRScraper()
        assert scraper.name == "BOAMP_FR"
        assert scraper.base_url == "https://www.boamp.fr"
        assert scraper.search_url == "https://www.boamp.fr/avis"

    @pytest.mark.asyncio
    async def test_parse_search_page(self, mock_html_content):
        """Test search page parsing."""
        scraper = BOAMPFRScraper()
        tenders = scraper._parse_search_page(mock_html_content)

        assert len(tenders) == 1
        assert tenders[0]["title"] == "Test BOAMP Tender"
        assert tenders[0]["url"] == "https://www.boamp.fr/avis/12345"
        assert tenders[0]["buyer_name"] == "Test BOAMP Organization"

    @pytest.mark.asyncio
    async def test_extract_tender_ref(self):
        """Test tender reference extraction."""
        scraper = BOAMPFRScraper()

        # Test URL-based extraction
        url = "https://www.boamp.fr/avis/12345"
        ref = scraper._extract_tender_ref(url, None)
        assert ref == "BOAMP_12345"

        # Test with mock element
        mock_element = MagicMock()
        mock_element.css_first.return_value = MagicMock()
        mock_element.css_first.return_value.text.return_value = "REF123"

        ref = scraper._extract_tender_ref("https://example.com", mock_element)
        assert ref == "BOAMP_REF123"

    @pytest.mark.asyncio
    async def test_extract_cpv_codes_from_html(self):
        """Test CPV code extraction from HTML."""
        scraper = BOAMPFRScraper()

        html_content = """
        <div class="cpv">CPV Code: 48000000</div>
        <span>Another CPV: 72000000</span>
        """

        from selectolax.parser import HTMLParser

        parser = HTMLParser(html_content)
        cpv_codes = scraper._extract_cpv_codes_from_html(parser)

        assert "48000000" in cpv_codes
        assert "72000000" in cpv_codes

    @pytest.mark.asyncio
    async def test_parse_tender_details(self):
        """Test tender details parsing."""
        scraper = BOAMPFRScraper()

        html_content = """
        <div class="summary">This is a detailed summary</div>
        <div class="deadline">20/02/2024</div>
        <div class="value">150000 €</div>
        """

        summary = {
            "tender_ref": "BOAMP_12345",
            "title": "Test Tender",
            "url": "https://example.com",
            "publication_date": None,
            "buyer_name": "Test Org",
            "value_amount": None,
        }

        tender = scraper._parse_tender_details(html_content, summary)

        assert tender is not None
        assert tender["tender_ref"] == "BOAMP_12345"
        assert tender["source"] == "BOAMP_FR"
        assert tender["summary"] == "This is a detailed summary"
        assert tender["buyer_country"] == "FR"
        assert tender["currency"] == "EUR"


class TestCommonScraper:
    """Test common scraper functionality."""

    @pytest.mark.asyncio
    async def test_date_parsing(self):
        """Test date parsing functionality."""
        from app.scrapers.common import BaseScraper

        scraper = BaseScraper("test")

        # Test various date formats
        assert scraper._parse_date("2024-01-15") == date(2024, 1, 15)
        assert scraper._parse_date("15/01/2024") == date(2024, 1, 15)
        assert scraper._parse_date("15-01-2024") == date(2024, 1, 15)
        assert scraper._parse_date("2024-01-15T10:30:00") == date(2024, 1, 15)
        assert scraper._parse_date("") is None
        assert scraper._parse_date("invalid") is None

    @pytest.mark.asyncio
    async def test_decimal_parsing(self):
        """Test decimal parsing functionality."""
        from app.scrapers.common import BaseScraper

        scraper = BaseScraper("test")

        assert scraper._parse_decimal("100000.50") == Decimal("100000.50")
        assert scraper._parse_decimal("€100,000.50") == Decimal("100000.50")
        assert scraper._parse_decimal("$100,000") == Decimal("100000")
        assert scraper._parse_decimal("") is None
        assert scraper._parse_decimal("invalid") is None

    @pytest.mark.asyncio
    async def test_cpv_normalization(self):
        """Test CPV code normalization."""
        from app.scrapers.common import BaseScraper

        scraper = BaseScraper("test")

        cpv_codes = ["48.00.00.00", "72000000", "48000001", "48000001"]  # Duplicate
        normalized = scraper._normalize_cpv_codes(cpv_codes)

        assert "48000000" in normalized
        assert "72000000" in normalized
        assert "48000001" in normalized
        assert len(normalized) == 3  # Duplicate removed

    @pytest.mark.asyncio
    async def test_country_normalization(self):
        """Test country code normalization."""
        from app.scrapers.common import BaseScraper

        scraper = BaseScraper("test")

        assert scraper._normalize_country_code("France") == "FR"
        assert scraper._normalize_country_code("FR") == "FR"
        assert scraper._normalize_country_code("United Kingdom") == "GB"
        assert scraper._normalize_country_code("") == "XX"
        assert scraper._normalize_country_code("Unknown") == "XX"

    @pytest.mark.asyncio
    async def test_text_cleaning(self):
        """Test text cleaning functionality."""
        from app.scrapers.common import BaseScraper

        scraper = BaseScraper("test")

        assert scraper._clean_text("  Test   text  ") == "Test text"
        assert scraper._clean_text("&amp; &lt; &gt;") == "& < >"
        assert scraper._clean_text("") == ""
        assert scraper._clean_text(None) == ""


class TestScraperIntegration:
    """Integration tests for scrapers."""

    @pytest.mark.asyncio
    async def test_fetch_last_tenders_function(self):
        """Test the convenience function for TED scraping."""
        with patch("app.scrapers.ted.TEDScraper") as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper.fetch_tenders.return_value = [{"test": "data"}]
            mock_scraper_class.return_value.__aenter__.return_value = mock_scraper

            result = await fetch_last_tenders(limit=10)

            assert result == [{"test": "data"}]
            mock_scraper.fetch_tenders.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_fetch_last_tenders_boamp_function(self):
        """Test the convenience function for BOAMP scraping."""
        with patch("app.scrapers.boamp_fr.BOAMPFRScraper") as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper.fetch_tenders.return_value = [{"test": "data"}]
            mock_scraper_class.return_value.__aenter__.return_value = mock_scraper

            result = await fetch_last_tenders_boamp(limit=10)

            assert result == [{"test": "data"}]
            mock_scraper.fetch_tenders.assert_called_once_with(10)
