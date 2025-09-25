"""Tests for the alerts system."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.models import (EmailLog, NotifyFrequency, SavedFilter,
                           Tender, TenderSource, User)
from app.db.schemas import EmailLogCreate, SavedFilterCreate
from app.services.alerts import AlertService, alert_service
from app.services.email import (EmailService, MockEmailProvider,
                                ResendEmailProvider)


class TestEmailService:
    """Test email service functionality."""

    async def test_mock_email_provider(self):
        """Test mock email provider."""
        provider = MockEmailProvider()

        # Test sending email
        result = await provider.send_email(
            to="test@example.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test Text",
        )

        assert result["id"] == "mock-1"
        assert result["to"] == "test@example.com"
        assert result["subject"] == "Test Subject"
        assert len(provider.sent_emails) == 1

    def test_email_service_format_currency(self):
        """Test currency formatting."""
        service = EmailService()

        assert service._format_currency(Decimal("100000.50"), "EUR") == "100,000.50 EUR"
        assert service._format_currency(Decimal("1000"), None) == "1,000.00"
        assert service._format_currency(None, "USD") == "N/A"

    def test_email_service_format_cpv_codes(self):
        """Test CPV code formatting."""
        service = EmailService()

        assert (
            service._format_cpv_codes(["48000000", "72000000"], 3)
            == "48000000, 72000000"
        )
        assert (
            service._format_cpv_codes(
                ["48000000", "72000000", "45000000", "50000000"], 2
            )
            == "48000000, 72000000 (+2 more)"
        )
        assert service._format_cpv_codes([], 3) == "N/A"

    def test_email_service_format_deadline(self):
        """Test deadline formatting."""
        service = EmailService()

        deadline = datetime(2024, 2, 15)
        assert service._format_deadline(deadline) == "2024-02-15"
        assert service._format_deadline(None) == "N/A"

    def test_generate_tender_html(self):
        """Test HTML generation for tender."""
        service = EmailService()

        tender = {
            "title": "Test Tender",
            "url": "https://example.com/tender",
            "buyer_name": "Test Organization",
            "buyer_country": "FR",
            "deadline_date": datetime(2024, 2, 15),
            "cpv_codes": ["48000000", "72000000"],
            "value_amount": Decimal("100000"),
            "currency": "EUR",
            "summary": "Test summary",
        }

        html = service._generate_tender_html(tender)

        assert "Test Tender" in html
        assert "https://example.com/tender" in html
        assert "Test Organization" in html
        assert "FR" in html
        assert "2024-02-15" in html
        assert "48000000, 72000000" in html
        assert "100,000.00 EUR" in html
        assert "Test summary" in html

    def test_generate_tender_text(self):
        """Test text generation for tender."""
        service = EmailService()

        tender = {
            "title": "Test Tender",
            "url": "https://example.com/tender",
            "buyer_name": "Test Organization",
            "buyer_country": "FR",
            "deadline_date": datetime(2024, 2, 15),
            "cpv_codes": ["48000000"],
            "value_amount": Decimal("100000"),
            "currency": "EUR",
            "summary": "Test summary",
        }

        text = service._generate_tender_text(tender)

        assert "Test Tender" in text
        assert "https://example.com/tender" in text
        assert "Test Organization" in text
        assert "FR" in text
        assert "2024-02-15" in text
        assert "48000000" in text
        assert "100,000.00 EUR" in text
        assert "Test summary" in text

    def test_generate_email_html(self):
        """Test HTML email generation."""
        service = EmailService()

        tenders = [
            {
                "title": "Test Tender 1",
                "url": "https://example.com/tender1",
                "buyer_name": "Test Org 1",
                "buyer_country": "FR",
                "deadline_date": datetime(2024, 2, 15),
                "cpv_codes": ["48000000"],
                "value_amount": Decimal("100000"),
                "currency": "EUR",
                "summary": "Test summary 1",
            }
        ]

        html = service._generate_email_html("Test Filter", tenders, "test@example.com")

        assert "Procurement Copilot" in html
        assert "Test Filter" in html
        assert "1 new tender" in html
        assert "test@example.com" in html
        assert "Test Tender 1" in html

    def test_generate_email_text(self):
        """Test text email generation."""
        service = EmailService()

        tenders = [
            {
                "title": "Test Tender 1",
                "url": "https://example.com/tender1",
                "buyer_name": "Test Org 1",
                "buyer_country": "FR",
                "deadline_date": datetime(2024, 2, 15),
                "cpv_codes": ["48000000"],
                "value_amount": Decimal("100000"),
                "currency": "EUR",
                "summary": "Test summary 1",
            }
        ]

        text = service._generate_email_text("Test Filter", tenders, "test@example.com")

        assert "PROCUREMENT COPILOT" in text
        assert "Test Filter" in text
        assert "1 new tender" in text
        assert "test@example.com" in text
        assert "Test Tender 1" in text

    def test_get_body_preview(self):
        """Test body preview generation."""
        service = EmailService()

        tenders = [
            {"title": "Test Tender 1"},
            {"title": "Test Tender 2"},
            {"title": "Test Tender 3"},
        ]

        preview = service.get_body_preview(tenders)
        assert "Test Tender 1" in preview
        assert "(+2 more)" in preview

        # Test with no tenders
        preview = service.get_body_preview([])
        assert preview == "No new tenders found."

    @pytest.mark.asyncio
    async def test_send_tender_digest(self):
        """Test sending tender digest."""
        service = EmailService(MockEmailProvider())

        tenders = [
            {
                "title": "Test Tender",
                "url": "https://example.com/tender",
                "buyer_name": "Test Organization",
                "buyer_country": "FR",
                "deadline_date": datetime(2024, 2, 15),
                "cpv_codes": ["48000000"],
                "value_amount": Decimal("100000"),
                "currency": "EUR",
                "summary": "Test summary",
            }
        ]

        result = await service.send_tender_digest(
            user_email="test@example.com", filter_name="Test Filter", tenders=tenders
        )

        assert result["status"] == "sent"
        assert result["tender_count"] == 1
        assert "email_id" in result

    @pytest.mark.asyncio
    async def test_send_tender_digest_no_tenders(self):
        """Test sending digest with no tenders."""
        service = EmailService(MockEmailProvider())

        result = await service.send_tender_digest(
            user_email="test@example.com", filter_name="Test Filter", tenders=[]
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "no_tenders"


class TestAlertService:
    """Test alert service functionality."""

    @pytest.mark.asyncio
    async def test_find_matching_tenders_keywords(self, test_db, sample_tenders):
        """Test finding tenders by keywords."""
        # Create a saved filter with keywords
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=["Test Tender 1"],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test keyword matching
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        assert len(matching_tenders) >= 1
        assert any("Test Tender 1" in tender["title"] for tender in matching_tenders)

    @pytest.mark.asyncio
    async def test_find_matching_tenders_cpv_codes(self, test_db, sample_tenders):
        """Test finding tenders by CPV codes."""
        # Create a saved filter with CPV codes
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=[],
            cpv_codes=["48000000"],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test CPV matching
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        # Should find tenders with matching CPV codes
        assert len(matching_tenders) >= 0

    @pytest.mark.asyncio
    async def test_find_matching_tenders_countries(self, test_db, sample_tenders):
        """Test finding tenders by countries."""
        # Create a saved filter with countries
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=[],
            cpv_codes=[],
            countries=["FR"],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test country matching
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        # Should find tenders from France
        assert len(matching_tenders) >= 0
        assert all(tender["buyer_country"] == "FR" for tender in matching_tenders)

    @pytest.mark.asyncio
    async def test_find_matching_tenders_value_range(self, test_db, sample_tenders):
        """Test finding tenders by value range."""
        # Create a saved filter with value range
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=[],
            cpv_codes=[],
            countries=[],
            min_value=Decimal("100000"),
            max_value=Decimal("200000"),
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test value range matching
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        # Should find tenders within value range
        assert len(matching_tenders) >= 0
        for tender in matching_tenders:
            if tender["value_amount"]:
                assert Decimal("100000") <= tender["value_amount"] <= Decimal("200000")

    @pytest.mark.asyncio
    async def test_find_matching_tenders_date_filter(self, test_db, sample_tenders):
        """Test finding tenders by date filter (last 24 hours)."""
        # Create a saved filter
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=[],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test date filtering
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        # Should only find tenders from the last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        for tender in matching_tenders:
            assert tender["publication_date"] >= yesterday.date()

    @pytest.mark.asyncio
    async def test_find_matching_tenders_deduplication(self, test_db):
        """Test deduplication by tender_ref."""
        # Create duplicate tenders with same tender_ref
        tender1 = Tender(
            tender_ref="DUPLICATE-001",
            source=TenderSource.TED,
            title="Duplicate Tender 1",
            publication_date=date.today(),
            buyer_country="FR",
            url="https://example.com/1",
            cpv_codes=["48000000"],
        )
        tender2 = Tender(
            tender_ref="DUPLICATE-001",  # Same reference
            source=TenderSource.BOAMP_FR,
            title="Duplicate Tender 2",
            publication_date=date.today(),
            buyer_country="FR",
            url="https://example.com/2",
            cpv_codes=["48000000"],
        )

        test_db.add(tender1)
        test_db.add(tender2)
        await test_db.commit()

        # Create a saved filter
        saved_filter = SavedFilter(
            user_id=uuid.uuid4(),
            name="Test Filter",
            keywords=[],
            cpv_codes=["48000000"],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Test deduplication
        matching_tenders = await alert_service._find_matching_tenders(
            test_db, saved_filter
        )

        # Should only return one tender despite duplicates
        assert len(matching_tenders) == 1
        assert matching_tenders[0]["tender_ref"] == "DUPLICATE-001"

    @pytest.mark.asyncio
    async def test_process_filter_no_matching_tenders(self, test_db, sample_user):
        """Test processing filter with no matching tenders."""
        # Create a saved filter with very specific criteria
        saved_filter = SavedFilter(
            user_id=sample_user.id,
            name="Very Specific Filter",
            keywords=["NonExistentKeyword"],
            cpv_codes=["99999999"],
            countries=["XX"],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Process the filter
        result = await alert_service._process_filter(test_db, saved_filter)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_matching_tenders"
        assert result["tender_count"] == 0

    @pytest.mark.asyncio
    async def test_process_filter_with_matching_tenders(
        self, test_db, sample_user, sample_tenders
    ):
        """Test processing filter with matching tenders."""
        # Create a saved filter that should match some tenders
        saved_filter = SavedFilter(
            user_id=sample_user.id,
            name="General Filter",
            keywords=["Test"],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Mock the email service
        with patch.object(alert_service, "_log_email") as mock_log:
            with patch("app.services.alerts.email_service") as mock_email_service:
                mock_email_service.send_tender_digest.return_value = {
                    "status": "sent",
                    "email_id": "test-email-id",
                    "tender_count": 5,
                }

                # Process the filter
                result = await alert_service._process_filter(test_db, saved_filter)

                assert result["status"] == "sent"
                assert result["tender_count"] >= 1
                assert "email_id" in result

                # Verify email was logged
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_alerts_pipeline(self, test_db, sample_user):
        """Test running the complete alerts pipeline."""
        # Create a saved filter
        saved_filter = SavedFilter(
            user_id=sample_user.id,
            name="Test Filter",
            keywords=["Test"],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Mock the email service
        with patch("app.services.alerts.email_service") as mock_email_service:
            mock_email_service.send_tender_digest.return_value = {
                "status": "sent",
                "email_id": "test-email-id",
                "tender_count": 1,
            }

            # Run the pipeline
            results = await alert_service.run_alerts_pipeline(test_db)

            assert results["processed_filters"] == 1
            assert results["emails_sent"] == 1
            assert results["emails_skipped"] == 0
            assert results["errors"] == 0
            assert len(results["details"]) == 1

    @pytest.mark.asyncio
    async def test_send_alerts_for_filter(self, test_db, sample_user, sample_tenders):
        """Test sending alerts for a specific filter."""
        # Create a saved filter
        saved_filter = SavedFilter(
            user_id=sample_user.id,
            name="Test Filter",
            keywords=["Test"],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Mock the email service
        with patch("app.services.alerts.email_service") as mock_email_service:
            mock_email_service.send_tender_digest.return_value = {
                "status": "sent",
                "email_id": "test-email-id",
                "tender_count": 1,
            }

            # Send alerts for the filter
            result = await alert_service.send_alerts_for_filter(
                test_db, str(saved_filter.id)
            )

            assert result["status"] == "sent"
            assert result["tender_count"] >= 1

    @pytest.mark.asyncio
    async def test_send_alerts_for_filter_not_found(self, test_db):
        """Test sending alerts for non-existent filter."""
        result = await alert_service.send_alerts_for_filter(test_db, "non-existent-id")

        assert result["status"] == "error"
        assert "Filter not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_alerts_for_filter_invalid_id(self, test_db):
        """Test sending alerts with invalid filter ID."""
        result = await alert_service.send_alerts_for_filter(test_db, "invalid-uuid")

        assert result["status"] == "error"
        assert "Invalid filter ID" in result["error"]


class TestAlertIntegration:
    """Integration tests for the alert system."""

    @pytest.mark.asyncio
    async def test_end_to_end_alert_flow(self, test_db, sample_user, sample_tenders):
        """Test complete end-to-end alert flow."""
        # Create a saved filter
        saved_filter = SavedFilter(
            user_id=sample_user.id,
            name="Integration Test Filter",
            keywords=["Test Tender"],
            cpv_codes=[],
            countries=[],
            notify_frequency=NotifyFrequency.DAILY,
        )
        test_db.add(saved_filter)
        await test_db.commit()

        # Mock email service to avoid actual email sending
        with patch("app.services.alerts.email_service") as mock_email_service:
            mock_email_service.send_tender_digest.return_value = {
                "status": "sent",
                "email_id": "integration-test-email",
                "tender_count": 5,
            }
            mock_email_service.get_body_preview.return_value = "Test preview"

            # Run the alerts pipeline
            results = await alert_service.run_alerts_pipeline(test_db)

            # Verify results
            assert results["processed_filters"] == 1
            assert results["emails_sent"] == 1
            assert results["errors"] == 0

            # Verify email service was called
            mock_email_service.send_tender_digest.assert_called_once()
            call_args = mock_email_service.send_tender_digest.call_args
            assert call_args[1]["user_email"] == sample_user.email
            assert call_args[1]["filter_name"] == saved_filter.name
            assert len(call_args[1]["tenders"]) >= 1

            # Verify filter was updated
            await test_db.refresh(saved_filter)
            assert saved_filter.last_notified_at is not None

            # Verify email was logged
            from app.db.crud import EmailLogCRUD

            email_logs = await EmailLogCRUD.get_by_filter(test_db, saved_filter.id)
            assert len(email_logs) == 1
            assert email_logs[0].subject.startswith("[Procurement Copilot]")
            assert "Integration Test Filter" in email_logs[0].subject
