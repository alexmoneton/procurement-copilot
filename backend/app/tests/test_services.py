"""Tests for services."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from app.services.cpv import CPVMapper, cpv_mapper
from app.services.dedupe import TenderDeduplicator, deduplicator
from app.services.ingest import IngestService, ingest_service


class TestCPVMapper:
    """Test CPV mapping functionality."""

    def test_cpv_mapper_init(self):
        """Test CPV mapper initialization."""
        mapper = CPVMapper()
        assert len(mapper.cpv_mappings) > 0
        assert len(mapper.keyword_mappings) > 0

    def test_get_cpv_info(self):
        """Test getting CPV information."""
        info = cpv_mapper.get_cpv_info("48000000")
        assert info is not None
        assert "name" in info
        assert "keywords" in info
        assert "Software package and information systems" in info["name"]

    def test_get_cpv_info_invalid(self):
        """Test getting CPV information for invalid code."""
        info = cpv_mapper.get_cpv_info("99999999")
        assert info is None

    def test_find_cpv_codes_by_keywords(self):
        """Test finding CPV codes by keywords."""
        text = "We need software development and IT services"
        codes = cpv_mapper.find_cpv_codes_by_keywords(text)

        assert len(codes) > 0
        assert "48000000" in codes  # Software package
        assert "72000000" in codes  # IT services

    def test_suggest_cpv_codes(self):
        """Test CPV code suggestion."""
        title = "Software Development Services"
        summary = "We need custom software development and IT consulting"

        codes = cpv_mapper.suggest_cpv_codes(title, summary)

        assert len(codes) > 0
        assert "48000000" in codes  # Software
        assert "72000000" in codes  # IT services

    def test_normalize_cpv_code(self):
        """Test CPV code normalization."""
        assert cpv_mapper._normalize_cpv_code("48.00.00.00") == "48000000"
        assert cpv_mapper._normalize_cpv_code("48000000") == "48000000"
        assert cpv_mapper._normalize_cpv_code("480000") == "48000000"
        assert cpv_mapper._normalize_cpv_code("") == ""

    def test_validate_cpv_codes(self):
        """Test CPV code validation."""
        codes = ["48000000", "72000000", "invalid", "48000001"]
        valid_codes = cpv_mapper.validate_cpv_codes(codes)

        assert "48000000" in valid_codes
        assert "72000000" in valid_codes
        assert "48000001" in valid_codes
        assert "invalid" not in valid_codes

    def test_get_cpv_hierarchy(self):
        """Test getting CPV hierarchy."""
        hierarchy = cpv_mapper.get_cpv_hierarchy("48000000")

        assert len(hierarchy) > 0
        assert any(item["code"] == "48000000" for item in hierarchy)
        assert any(
            item["code"] == "48000000" for item in hierarchy
        )  # Parent categories


class TestTenderDeduplicator:
    """Test deduplication functionality."""

    def test_deduplicator_init(self):
        """Test deduplicator initialization."""
        dedup = TenderDeduplicator()
        assert dedup is not None

    def test_text_similarity(self):
        """Test text similarity calculation."""
        dedup = TenderDeduplicator()

        # Identical texts
        assert (
            dedup._text_similarity("Software Development", "Software Development")
            == 1.0
        )

        # Similar texts
        similarity = dedup._text_similarity(
            "Software Development", "Software Development Services"
        )
        assert 0.5 < similarity < 1.0

        # Different texts
        similarity = dedup._text_similarity("Software Development", "Construction Work")
        assert similarity < 0.5

        # Empty texts
        assert dedup._text_similarity("", "") == 0.0
        assert dedup._text_similarity("Software", "") == 0.0

    def test_cpv_similarity(self):
        """Test CPV codes similarity calculation."""
        dedup = TenderDeduplicator()

        # Identical CPV codes
        assert dedup._cpv_similarity(["48000000"], ["48000000"]) == 1.0

        # Overlapping CPV codes
        similarity = dedup._cpv_similarity(
            ["48000000", "72000000"], ["48000000", "45000000"]
        )
        assert similarity == 0.5  # 1 out of 3 unique codes

        # No overlap
        assert dedup._cpv_similarity(["48000000"], ["72000000"]) == 0.0

        # Empty lists
        assert dedup._cpv_similarity([], []) == 0.0

    def test_value_similarity(self):
        """Test value similarity calculation."""
        dedup = TenderDeduplicator()

        # Identical values
        assert dedup._value_similarity(100000, 100000) == 1.0

        # Similar values
        similarity = dedup._value_similarity(100000, 110000)
        assert 0.8 < similarity < 1.0

        # Very different values
        similarity = dedup._value_similarity(100000, 1000000)
        assert similarity < 0.5

        # Missing values
        assert dedup._value_similarity(None, 100000) == 0.5
        assert dedup._value_similarity(100000, None) == 0.5
        assert dedup._value_similarity(None, None) == 0.5

    def test_calculate_similarity(self):
        """Test overall similarity calculation."""
        dedup = TenderDeduplicator()

        tender1 = {
            "title": "Software Development Services",
            "buyer_name": "Test Organization",
            "cpv_codes": ["48000000"],
            "value_amount": 100000,
        }

        tender2 = {
            "title": "Software Development Services",
            "buyer_name": "Test Organization",
            "cpv_codes": ["48000000"],
            "value_amount": 100000,
        }

        similarity = dedup._calculate_similarity(tender1, tender2)
        assert similarity > 0.9  # Very similar

        # Different tender
        tender3 = {
            "title": "Construction Work",
            "buyer_name": "Different Organization",
            "cpv_codes": ["45000000"],
            "value_amount": 500000,
        }

        similarity = dedup._calculate_similarity(tender1, tender3)
        assert similarity < 0.5  # Not similar

    def test_find_duplicates(self):
        """Test finding duplicates in a list of tenders."""
        dedup = TenderDeduplicator()

        tenders = [
            {
                "tender_ref": "TEST-001",
                "title": "Software Development",
                "buyer_name": "Test Org",
                "cpv_codes": ["48000000"],
                "value_amount": 100000,
            },
            {
                "tender_ref": "TEST-002",
                "title": "Software Development Services",  # Similar title
                "buyer_name": "Test Organization",  # Similar buyer
                "cpv_codes": ["48000000"],
                "value_amount": 100000,
            },
            {
                "tender_ref": "TEST-003",
                "title": "Construction Work",  # Different
                "buyer_name": "Different Org",
                "cpv_codes": ["45000000"],
                "value_amount": 500000,
            },
        ]

        duplicates = dedup.find_duplicates(tenders, similarity_threshold=0.8)

        assert len(duplicates) == 1  # TEST-001 and TEST-002 should be duplicates
        assert duplicates[0][2] > 0.8  # High similarity score

    def test_generate_fingerprint(self):
        """Test fingerprint generation."""
        dedup = TenderDeduplicator()

        tender = {
            "title": "Software Development",
            "buyer_name": "Test Org",
            "cpv_codes": ["48000000"],
            "buyer_country": "FR",
        }

        fingerprint = dedup.generate_fingerprint(tender)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 32  # MD5 hash length

        # Same tender should generate same fingerprint
        fingerprint2 = dedup.generate_fingerprint(tender)
        assert fingerprint == fingerprint2

    def test_group_by_fingerprint(self):
        """Test grouping tenders by fingerprint."""
        dedup = TenderDeduplicator()

        tenders = [
            {
                "title": "Software Development",
                "buyer_name": "Test Org",
                "cpv_codes": ["48000000"],
                "buyer_country": "FR",
            },
            {
                "title": "Software Development",  # Same content
                "buyer_name": "Test Org",
                "cpv_codes": ["48000000"],
                "buyer_country": "FR",
            },
            {
                "title": "Construction Work",  # Different
                "buyer_name": "Different Org",
                "cpv_codes": ["45000000"],
                "buyer_country": "DE",
            },
        ]

        groups = dedup.group_by_fingerprint(tenders)

        assert len(groups) == 2  # Two unique fingerprints
        assert any(
            len(group) == 2 for group in groups.values()
        )  # One group has 2 items

    def test_select_best_tender(self):
        """Test selecting the best tender from a group."""
        dedup = TenderDeduplicator()

        tenders = [
            {
                "title": "Software Development",  # Minimal info
                "buyer_name": None,
                "cpv_codes": [],
                "value_amount": None,
                "url": "",
            },
            {
                "title": "Software Development Services",  # More complete
                "buyer_name": "Test Organization",
                "cpv_codes": ["48000000"],
                "value_amount": 100000,
                "url": "https://example.com",
            },
        ]

        best = dedup.select_best_tender(tenders)

        # Should select the more complete tender
        assert best["buyer_name"] == "Test Organization"
        assert best["cpv_codes"] == ["48000000"]
        assert best["value_amount"] == 100000

    def test_deduplicate_tenders(self):
        """Test full deduplication process."""
        dedup = TenderDeduplicator()

        tenders = [
            {
                "tender_ref": "TEST-001",
                "title": "Software Development",
                "buyer_name": "Test Org",
                "cpv_codes": ["48000000"],
                "value_amount": 100000,
            },
            {
                "tender_ref": "TEST-002",
                "title": "Software Development Services",  # Similar
                "buyer_name": "Test Organization",
                "cpv_codes": ["48000000"],
                "value_amount": 100000,
            },
            {
                "tender_ref": "TEST-003",
                "title": "Construction Work",  # Different
                "buyer_name": "Different Org",
                "cpv_codes": ["45000000"],
                "value_amount": 500000,
            },
        ]

        deduplicated = dedup.deduplicate_tenders(tenders)

        assert len(deduplicated) == 2  # Should remove 1 duplicate
        assert any(
            t["tender_ref"] == "TEST-003" for t in deduplicated
        )  # Unique tender kept


class TestIngestService:
    """Test ingestion service functionality."""

    @pytest.mark.asyncio
    async def test_ingest_service_init(self):
        """Test ingest service initialization."""
        service = IngestService()
        assert service is not None

    def test_normalize_tender(self):
        """Test tender normalization."""
        service = IngestService()

        raw_tender = {
            "tender_ref": "TEST-001",
            "source": "TED",
            "title": "  Software Development  ",
            "summary": "  Test summary  ",
            "publication_date": "2024-01-15",
            "deadline_date": "2024-02-15",
            "cpv_codes": ["48.00.00.00"],
            "buyer_name": "  Test Organization  ",
            "buyer_country": "france",
            "value_amount": "100000.50",
            "currency": "eur",
            "url": "  https://example.com  ",
        }

        normalized = service._normalize_tender(raw_tender)

        assert normalized is not None
        assert normalized["tender_ref"] == "TEST-001"
        assert normalized["title"] == "Software Development"  # Trimmed
        assert normalized["summary"] == "Test summary"  # Trimmed
        assert normalized["buyer_name"] == "Test Organization"  # Trimmed
        assert normalized["buyer_country"] == "FR"  # Normalized
        assert normalized["currency"] == "EUR"  # Normalized
        assert normalized["url"] == "https://example.com"  # Trimmed
        assert "48000000" in normalized["cpv_codes"]  # Normalized

    def test_normalize_tender_missing_required_fields(self):
        """Test normalization with missing required fields."""
        service = IngestService()

        raw_tender = {
            "tender_ref": "",  # Missing
            "title": "Test Tender",
        }

        normalized = service._normalize_tender(raw_tender)
        assert normalized is None

    def test_clean_text(self):
        """Test text cleaning functionality."""
        service = IngestService()

        assert service._clean_text("  Test   text  ") == "Test text"
        assert service._clean_text("&amp; &lt; &gt;") == "& < >"
        assert service._clean_text("") == ""
        assert service._clean_text(None) == ""

    @pytest.mark.asyncio
    async def test_process_tenders(self):
        """Test tender processing."""
        service = IngestService()

        raw_tenders = [
            {
                "tender_ref": "TEST-001",
                "source": "TED",
                "title": "Test Tender 1",
                "publication_date": "2024-01-15",
                "buyer_country": "FR",
                "url": "https://example.com/1",
            },
            {
                "tender_ref": "",  # Invalid
                "title": "Test Tender 2",
            },
            {
                "tender_ref": "TEST-003",
                "source": "TED",
                "title": "Test Tender 3",
                "publication_date": "2024-01-16",
                "buyer_country": "DE",
                "url": "https://example.com/3",
            },
        ]

        processed = await service._process_tenders(raw_tenders)

        assert len(processed) == 2  # One invalid tender filtered out
        assert any(t["tender_ref"] == "TEST-001" for t in processed)
        assert any(t["tender_ref"] == "TEST-003" for t in processed)

    @pytest.mark.asyncio
    async def test_run_ingest_success(self, test_db):
        """Test successful ingestion run."""
        service = IngestService()

        # Mock the scraper functions
        with (
            patch("app.services.ingest.fetch_last_tenders") as mock_ted,
            patch("app.services.ingest.fetch_last_tenders_boamp") as mock_boamp,
        ):

            mock_ted.return_value = [
                {
                    "tender_ref": "TED-001",
                    "source": "TED",
                    "title": "TED Test Tender",
                    "publication_date": "2024-01-15",
                    "buyer_country": "FR",
                    "url": "https://example.com/ted-001",
                }
            ]

            mock_boamp.return_value = [
                {
                    "tender_ref": "BOAMP-001",
                    "source": "BOAMP_FR",
                    "title": "BOAMP Test Tender",
                    "publication_date": "2024-01-15",
                    "buyer_country": "FR",
                    "url": "https://example.com/boamp-001",
                }
            ]

            results = await service.run_ingest(test_db, ted_limit=10, boamp_limit=10)

            assert results["inserted"] >= 2  # At least 2 tenders inserted
            assert results["updated"] == 0  # No updates on first run
            assert results["errors"] == 0  # No errors

    @pytest.mark.asyncio
    async def test_run_ingest_scraper_error(self, test_db):
        """Test ingestion with scraper errors."""
        service = IngestService()

        # Mock scraper functions to raise errors
        with (
            patch("app.services.ingest.fetch_last_tenders") as mock_ted,
            patch("app.services.ingest.fetch_last_tenders_boamp") as mock_boamp,
        ):

            mock_ted.side_effect = Exception("TED scraper error")
            mock_boamp.side_effect = Exception("BOAMP scraper error")

            results = await service.run_ingest(test_db, ted_limit=10, boamp_limit=10)

            assert results["inserted"] == 0
            assert results["updated"] == 0
            assert results["skipped"] == 0
            assert (
                results["errors"] == 0
            )  # Errors are logged but not counted in results
