"""Tests for outreach functionality."""

import pytest
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.outreach import OutreachTargetingService, outreach_targeting_service
from app.services.outreach_templates import OutreachTemplates, outreach_templates
from app.services.company_resolution import CompanyResolutionService, company_resolution_service
from app.services.outreach_engine import OutreachEngine, outreach_engine
from app.db.models import Award, Company, Tender, TenderSource
from app.db.schemas import AwardCreate, CompanyCreate
from app.db.crud import AwardCRUD, CompanyCRUD


@pytest.fixture
def sample_awards():
    """Sample award data for testing."""
    return [
        {
            "tender_ref": "TED-2023-001",
            "award_date": date.today() - timedelta(days=30),
            "winner_names": ["Winner Corp"],
            "other_bidders": ["Loser Corp 1", "Loser Corp 2"],
            "cpv_codes": ["72000000"],
            "buyer_country": "FR",
            "buyer_name": "French Ministry",
            "value_amount": Decimal("100000.00"),
            "currency": "EUR",
            "title": "IT Services Contract"
        },
        {
            "tender_ref": "TED-2023-002",
            "award_date": date.today() - timedelta(days=60),
            "winner_names": ["Another Winner"],
            "other_bidders": ["Loser Corp 1", "Loser Corp 3"],
            "cpv_codes": ["72000000"],
            "buyer_country": "FR",
            "buyer_name": "French Agency",
            "value_amount": Decimal("200000.00"),
            "currency": "EUR",
            "title": "Software Development"
        }
    ]


@pytest.fixture
def sample_tenders():
    """Sample tender data for testing."""
    return [
        Tender(
            id=uuid.uuid4(),
            tender_ref="TED-2023-001",
            source=TenderSource.TED,
            title="IT Services Contract",
            summary="IT services for government",
            publication_date=date.today() - timedelta(days=45),
            deadline_date=date.today() - timedelta(days=30),
            cpv_codes=["72000000"],
            buyer_name="French Ministry",
            buyer_country="FR",
            value_amount=Decimal("100000.00"),
            currency="EUR",
            url="https://example.com/tender1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Tender(
            id=uuid.uuid4(),
            tender_ref="TED-2023-002",
            source=TenderSource.TED,
            title="Software Development",
            summary="Software development services",
            publication_date=date.today() - timedelta(days=75),
            deadline_date=date.today() - timedelta(days=60),
            cpv_codes=["72000000"],
            buyer_name="French Agency",
            buyer_country="FR",
            value_amount=Decimal("200000.00"),
            currency="EUR",
            url="https://example.com/tender2",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]


@pytest.fixture
def sample_companies():
    """Sample company data for testing."""
    return [
        Company(
            id=uuid.uuid4(),
            name="Loser Corp 1",
            domain="losercorp1.com",
            email="contact@losercorp1.com",
            country="FR",
            is_suppressed=False,
            last_contacted=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Company(
            id=uuid.uuid4(),
            name="Loser Corp 2",
            domain="losercorp2.com",
            email="contact@losercorp2.com",
            country="FR",
            is_suppressed=False,
            last_contacted=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]


class TestOutreachTargetingService:
    """Test outreach targeting service."""
    
    @pytest.mark.asyncio
    async def test_get_active_but_losing_smes(self, test_db: AsyncMock, sample_awards, sample_tenders):
        """Test finding active but losing SMEs."""
        # Mock database queries
        test_db.execute.return_value.scalars.return_value.all.return_value = sample_awards
        
        # Mock tender queries
        with patch('app.services.outreach.TenderCRUD') as mock_tender_crud:
            mock_tender_crud.search_tenders.return_value = sample_tenders
            
            service = OutreachTargetingService()
            leads = await service.get_active_but_losing_smes(
                test_db, cpv_codes=["72000000"], country="FR", limit=10
            )
            
            assert len(leads) > 0
            assert "Loser Corp 1" in [lead["name"] for lead in leads]
            assert "Loser Corp 2" in [lead["name"] for lead in leads]
    
    @pytest.mark.asyncio
    async def test_get_single_country_bidders_with_cross_border_potential(self, test_db: AsyncMock):
        """Test finding cross-border potential companies."""
        # Mock database queries
        test_db.execute.return_value.scalars.return_value.all.return_value = []
        
        service = OutreachTargetingService()
        leads = await service.get_single_country_bidders_with_cross_border_potential(
            test_db, cpv_codes=["72000000"], limit=10
        )
        
        assert isinstance(leads, list)
    
    @pytest.mark.asyncio
    async def test_get_lapsed_bidders(self, test_db: AsyncMock):
        """Test finding lapsed bidders."""
        # Mock database queries
        test_db.execute.return_value.scalars.return_value.all.return_value = []
        
        service = OutreachTargetingService()
        leads = await service.get_lapsed_bidders(
            test_db, cpv_codes=["72000000"], country="FR", limit=10
        )
        
        assert isinstance(leads, list)
    
    def test_get_neighbor_countries(self):
        """Test neighbor country mapping."""
        service = OutreachTargetingService()
        
        # Test France neighbors
        neighbors = service._get_neighbor_countries("FR")
        assert "ES" in neighbors
        assert "IT" in neighbors
        assert "DE" in neighbors
        
        # Test Germany neighbors
        neighbors = service._get_neighbor_countries("DE")
        assert "FR" in neighbors
        assert "NL" in neighbors
        assert "PL" in neighbors
        
        # Test unknown country
        neighbors = service._get_neighbor_countries("XX")
        assert neighbors == []


class TestOutreachTemplates:
    """Test outreach email templates."""
    
    def test_generate_missed_opportunities_email(self):
        """Test missed opportunities email generation."""
        templates = OutreachTemplates()
        
        email = templates.generate_missed_opportunities_email(
            company_name="Test Corp",
            sector="IT Services",
            missed_tenders=[
                {"title": "Missed Tender 1", "country": "FR"},
                {"title": "Missed Tender 2", "country": "DE"}
            ],
            upcoming_tenders=[
                {"title": "Upcoming Tender 1", "deadline": date.today() + timedelta(days=7)},
                {"title": "Upcoming Tender 2", "deadline": date.today() + timedelta(days=14)}
            ]
        )
        
        assert "Test Corp" in email["subject"]
        assert "IT Services" in email["subject"]
        assert "Test Corp" in email["html_content"]
        assert "Test Corp" in email["text_content"]
        assert "Missed Tender 1" in email["html_content"]
        assert "Upcoming Tender 1" in email["html_content"]
    
    def test_generate_cross_border_expansion_email(self):
        """Test cross-border expansion email generation."""
        templates = OutreachTemplates()
        
        email = templates.generate_cross_border_expansion_email(
            company_name="Test Corp",
            home_country="France",
            adjacent_country="Germany",
            upcoming_tenders=[
                {"title": "German Tender 1", "deadline": date.today() + timedelta(days=7), "value": 50000, "currency": "EUR"}
            ]
        )
        
        assert "France" in email["subject"]
        assert "Germany" in email["subject"]
        assert "Test Corp" in email["html_content"]
        assert "German Tender 1" in email["html_content"]
    
    def test_generate_reactivation_email(self):
        """Test reactivation email generation."""
        templates = OutreachTemplates()
        
        email = templates.generate_reactivation_email(
            company_name="Test Corp",
            sector="IT Services",
            upcoming_tenders=[
                {"title": "Reactivation Tender 1", "deadline": date.today() + timedelta(days=7), "value": 75000, "currency": "EUR", "country": "FR"}
            ]
        )
        
        assert "Test Corp" in email["subject"]
        assert "IT Services" in email["subject"]
        assert "Test Corp" in email["html_content"]
        assert "Reactivation Tender 1" in email["html_content"]


class TestCompanyResolutionService:
    """Test company resolution service."""
    
    @pytest.mark.asyncio
    async def test_resolve_company_from_name(self, test_db: AsyncMock):
        """Test company resolution from name."""
        # Mock existing company
        existing_company = Company(
            id=uuid.uuid4(),
            name="Test Corp",
            domain="testcorp.com",
            email="contact@testcorp.com",
            country="FR",
            is_suppressed=False,
            last_contacted=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with patch('app.services.company_resolution.CompanyCRUD.get_by_name_and_country') as mock_get:
            mock_get.return_value = existing_company
            
            service = CompanyResolutionService()
            result = await service.resolve_company_from_name(test_db, "Test Corp", "FR")
            
            assert result is not None
            assert result["name"] == "Test Corp"
            assert result["domain"] == "testcorp.com"
            assert result["email"] == "contact@testcorp.com"
    
    @pytest.mark.asyncio
    async def test_import_companies_from_csv(self, test_db: AsyncMock):
        """Test CSV import functionality."""
        csv_content = """name,domain,email,country
Test Corp 1,testcorp1.com,contact@testcorp1.com,FR
Test Corp 2,testcorp2.com,contact@testcorp2.com,DE
Test Corp 3,,contact@testcorp3.com,IT"""
        
        with patch('app.services.company_resolution.CompanyCRUD.get_by_name_and_country') as mock_get:
            with patch('app.services.company_resolution.CompanyCRUD.create') as mock_create:
                with patch('app.services.company_resolution.CompanyCRUD.update') as mock_update:
                    mock_get.return_value = None  # No existing companies
                    mock_create.return_value = Company(
                        id=uuid.uuid4(),
                        name="Test Corp",
                        domain="testcorp.com",
                        email="contact@testcorp.com",
                        country="FR",
                        is_suppressed=False,
                        last_contacted=None,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    service = CompanyResolutionService()
                    results = await service.import_companies_from_csv(test_db, csv_content, has_header=True)
                    
                    assert results["imported"] == 3
                    assert results["updated"] == 0
                    assert results["errors"] == 0
    
    def test_validate_company_data(self):
        """Test company data validation."""
        service = CompanyResolutionService()
        
        # Valid data
        valid_data = {
            "name": "Test Corp",
            "country": "FR",
            "domain": "testcorp.com",
            "email": "contact@testcorp.com"
        }
        
        result = service.validate_company_data(valid_data)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        
        # Invalid data
        invalid_data = {
            "name": "",
            "country": "INVALID",
            "domain": "invalid-domain",
            "email": "invalid-email"
        }
        
        result = service.validate_company_data(invalid_data)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestOutreachEngine:
    """Test outreach engine."""
    
    @pytest.mark.asyncio
    async def test_build_lead_list(self, test_db: AsyncMock):
        """Test lead list building."""
        with patch('app.services.outreach_engine.outreach_targeting_service.get_active_but_losing_smes') as mock_get:
            mock_get.return_value = [
                {"name": "Test Corp 1", "bid_count": 3},
                {"name": "Test Corp 2", "bid_count": 2}
            ]
            
            engine = OutreachEngine()
            leads = await engine.build_lead_list(
                test_db, "lost_bidders", cpv_codes=["72000000"], country="FR", limit=10
            )
            
            assert len(leads) == 2
            assert leads[0]["name"] == "Test Corp 1"
            assert leads[1]["name"] == "Test Corp 2"
    
    @pytest.mark.asyncio
    async def test_send_campaign(self, test_db: AsyncMock):
        """Test campaign sending."""
        leads = [
            {"name": "Test Corp 1", "bid_count": 3},
            {"name": "Test Corp 2", "bid_count": 2}
        ]
        
        with patch('app.services.outreach_engine.outreach_engine._process_lead') as mock_process:
            mock_process.return_value = {"status": "sent", "email_id": "test-email-id"}
            
            engine = OutreachEngine()
            results = await engine.send_campaign(
                test_db, "missed_opportunities", leads, limit=2
            )
            
            assert results["sent"] == 2
            assert results["failed"] == 0
            assert results["skipped"] == 0
            assert results["total_leads"] == 2
    
    @pytest.mark.asyncio
    async def test_process_lead_success(self, test_db: AsyncMock):
        """Test successful lead processing."""
        lead = {"name": "Test Corp", "bid_count": 3}
        
        with patch('app.services.outreach_engine.company_resolution_service.resolve_company_from_name') as mock_resolve:
            with patch('app.services.outreach_engine.outreach_targeting_service.get_upcoming_tenders_for_company') as mock_tenders:
                with patch('app.services.outreach_engine.email_service.send_alert_email') as mock_email:
                    with patch('app.services.outreach_engine.EmailLogCRUD.create') as mock_log:
                        with patch('app.services.outreach_engine.CompanyCRUD.update_last_contacted') as mock_update:
                            mock_resolve.return_value = {
                                "id": uuid.uuid4(),
                                "name": "Test Corp",
                                "email": "contact@testcorp.com",
                                "is_suppressed": False
                            }
                            mock_tenders.return_value = []
                            mock_email.return_value = {"id": "test-email-id"}
                            mock_log.return_value = None
                            mock_update.return_value = True
                            
                            engine = OutreachEngine()
                            result = await engine._process_lead(
                                test_db, "missed_opportunities", lead
                            )
                            
                            assert result["status"] == "sent"
                            assert result["email_id"] == "test-email-id"
    
    @pytest.mark.asyncio
    async def test_process_lead_skipped_no_email(self, test_db: AsyncMock):
        """Test lead processing skipped due to no email."""
        lead = {"name": "Test Corp", "bid_count": 3}
        
        with patch('app.services.outreach_engine.company_resolution_service.resolve_company_from_name') as mock_resolve:
            mock_resolve.return_value = {
                "id": uuid.uuid4(),
                "name": "Test Corp",
                "email": None,  # No email
                "is_suppressed": False
            }
            
            engine = OutreachEngine()
            result = await engine._process_lead(
                test_db, "missed_opportunities", lead
            )
            
            assert result["status"] == "skipped"
            assert "No email address" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_process_lead_skipped_suppressed(self, test_db: AsyncMock):
        """Test lead processing skipped due to suppression."""
        lead = {"name": "Test Corp", "bid_count": 3}
        
        with patch('app.services.outreach_engine.company_resolution_service.resolve_company_from_name') as mock_resolve:
            mock_resolve.return_value = {
                "id": uuid.uuid4(),
                "name": "Test Corp",
                "email": "contact@testcorp.com",
                "is_suppressed": True  # Suppressed
            }
            
            engine = OutreachEngine()
            result = await engine._process_lead(
                test_db, "missed_opportunities", lead
            )
            
            assert result["status"] == "skipped"
            assert "Company is suppressed" in result["reason"]


@pytest.mark.asyncio
async def test_integration_outreach_workflow(test_db: AsyncMock):
    """Test complete outreach workflow integration."""
    # This test would integrate all components
    # For now, it's a placeholder for future integration tests
    
    # Mock all the services
    with patch('app.services.outreach_engine.outreach_targeting_service') as mock_targeting:
        with patch('app.services.outreach_engine.company_resolution_service') as mock_resolution:
            with patch('app.services.outreach_engine.email_service') as mock_email:
                mock_targeting.get_active_but_losing_smes.return_value = [
                    {"name": "Integration Test Corp", "bid_count": 3}
                ]
                mock_resolution.resolve_company_from_name.return_value = {
                    "id": uuid.uuid4(),
                    "name": "Integration Test Corp",
                    "email": "contact@integrationtest.com",
                    "is_suppressed": False
                }
                mock_email.send_alert_email.return_value = {"id": "integration-email-id"}
                
                engine = OutreachEngine()
                
                # Build leads
                leads = await engine.build_lead_list(
                    test_db, "lost_bidders", limit=1
                )
                assert len(leads) == 1
                
                # Send campaign
                results = await engine.send_campaign(
                    test_db, "missed_opportunities", leads, limit=1
                )
                assert results["sent"] == 1
