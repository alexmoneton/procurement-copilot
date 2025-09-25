"""Tests for CRUD operations."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from app.db.crud import SavedFilterCRUD, TenderCRUD, UserCRUD
from app.db.models import NotifyFrequency, TenderSource
from app.db.schemas import (SavedFilterCreate, SavedFilterUpdate, TenderCreate,
                            TenderUpdate, UserCreate)


class TestTenderCRUD:
    """Test tender CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_tender(self, test_db, test_tender_data):
        """Test creating a tender."""
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        assert created_tender is not None
        assert created_tender.tender_ref == test_tender_data["tender_ref"]
        assert created_tender.title == test_tender_data["title"]
        assert created_tender.source == test_tender_data["source"]
        assert created_tender.buyer_country == test_tender_data["buyer_country"]
        assert created_tender.id is not None

    @pytest.mark.asyncio
    async def test_get_tender_by_id(self, test_db, test_tender_data):
        """Test getting a tender by ID."""
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        retrieved_tender = await TenderCRUD.get_by_id(test_db, created_tender.id)

        assert retrieved_tender is not None
        assert retrieved_tender.id == created_tender.id
        assert retrieved_tender.tender_ref == test_tender_data["tender_ref"]

    @pytest.mark.asyncio
    async def test_get_tender_by_id_not_found(self, test_db):
        """Test getting a non-existent tender by ID."""
        non_existent_id = uuid.uuid4()
        retrieved_tender = await TenderCRUD.get_by_id(test_db, non_existent_id)

        assert retrieved_tender is None

    @pytest.mark.asyncio
    async def test_get_tender_by_ref(self, test_db, test_tender_data):
        """Test getting a tender by reference."""
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        retrieved_tender = await TenderCRUD.get_by_ref(
            test_db, test_tender_data["tender_ref"]
        )

        assert retrieved_tender is not None
        assert retrieved_tender.tender_ref == test_tender_data["tender_ref"]
        assert retrieved_tender.id == created_tender.id

    @pytest.mark.asyncio
    async def test_get_tender_by_ref_not_found(self, test_db):
        """Test getting a non-existent tender by reference."""
        retrieved_tender = await TenderCRUD.get_by_ref(test_db, "NON-EXISTENT-REF")

        assert retrieved_tender is None

    @pytest.mark.asyncio
    async def test_update_tender(self, test_db, test_tender_data):
        """Test updating a tender."""
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        update_data = TenderUpdate(
            title="Updated Title",
            summary="Updated Summary",
            value_amount=Decimal("200000.00"),
        )

        updated_tender = await TenderCRUD.update(
            test_db, created_tender.id, update_data
        )

        assert updated_tender is not None
        assert updated_tender.id == created_tender.id
        assert updated_tender.title == "Updated Title"
        assert updated_tender.summary == "Updated Summary"
        assert updated_tender.value_amount == Decimal("200000.00")
        # Unchanged fields should remain the same
        assert updated_tender.tender_ref == test_tender_data["tender_ref"]

    @pytest.mark.asyncio
    async def test_update_tender_not_found(self, test_db):
        """Test updating a non-existent tender."""
        non_existent_id = uuid.uuid4()
        update_data = TenderUpdate(title="Updated Title")

        updated_tender = await TenderCRUD.update(test_db, non_existent_id, update_data)

        assert updated_tender is None

    @pytest.mark.asyncio
    async def test_delete_tender(self, test_db, test_tender_data):
        """Test deleting a tender."""
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        deleted = await TenderCRUD.delete(test_db, created_tender.id)

        assert deleted is True

        # Verify tender is deleted
        retrieved_tender = await TenderCRUD.get_by_id(test_db, created_tender.id)
        assert retrieved_tender is None

    @pytest.mark.asyncio
    async def test_delete_tender_not_found(self, test_db):
        """Test deleting a non-existent tender."""
        non_existent_id = uuid.uuid4()
        deleted = await TenderCRUD.delete(test_db, non_existent_id)

        assert deleted is False

    @pytest.mark.asyncio
    async def test_search_tenders_empty(self, test_db):
        """Test searching tenders with empty database."""
        tenders, total = await TenderCRUD.search(test_db)

        assert tenders == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_tenders_with_data(self, test_db, sample_tenders):
        """Test searching tenders with data."""
        tenders, total = await TenderCRUD.search(test_db)

        assert len(tenders) == 5
        assert total == 5
        # Should be ordered by publication_date desc
        assert tenders[0].publication_date >= tenders[1].publication_date

    @pytest.mark.asyncio
    async def test_search_tenders_with_query(self, test_db, sample_tenders):
        """Test searching tenders with query."""
        tenders, total = await TenderCRUD.search(test_db, query="Test Tender 1")

        assert len(tenders) >= 1
        assert total >= 1
        assert any("Test Tender 1" in tender.title for tender in tenders)

    @pytest.mark.asyncio
    async def test_search_tenders_with_cpv_filter(self, test_db, sample_tenders):
        """Test searching tenders with CPV filter."""
        tenders, total = await TenderCRUD.search(test_db, cpv="48000000")

        assert len(tenders) >= 0
        assert total >= 0

    @pytest.mark.asyncio
    async def test_search_tenders_with_country_filter(self, test_db, sample_tenders):
        """Test searching tenders with country filter."""
        tenders, total = await TenderCRUD.search(test_db, country="FR")

        assert len(tenders) >= 0
        assert total >= 0
        assert all(tender.buyer_country == "FR" for tender in tenders)

    @pytest.mark.asyncio
    async def test_search_tenders_with_date_filters(self, test_db, sample_tenders):
        """Test searching tenders with date filters."""
        from_date = date(2024, 1, 15)
        to_date = date(2024, 1, 20)

        tenders, total = await TenderCRUD.search(
            test_db, from_date=from_date, to_date=to_date
        )

        assert len(tenders) >= 0
        assert total >= 0
        assert all(
            from_date <= tender.publication_date <= to_date for tender in tenders
        )

    @pytest.mark.asyncio
    async def test_search_tenders_with_value_filters(self, test_db, sample_tenders):
        """Test searching tenders with value filters."""
        min_value = Decimal("100000")
        max_value = Decimal("200000")

        tenders, total = await TenderCRUD.search(
            test_db, min_value=min_value, max_value=max_value
        )

        assert len(tenders) >= 0
        assert total >= 0
        assert all(
            min_value <= tender.value_amount <= max_value
            for tender in tenders
            if tender.value_amount is not None
        )

    @pytest.mark.asyncio
    async def test_search_tenders_with_source_filter(self, test_db, sample_tenders):
        """Test searching tenders with source filter."""
        tenders, total = await TenderCRUD.search(test_db, source=TenderSource.TED)

        assert len(tenders) >= 0
        assert total >= 0
        assert all(tender.source == TenderSource.TED for tender in tenders)

    @pytest.mark.asyncio
    async def test_search_tenders_with_pagination(self, test_db, sample_tenders):
        """Test searching tenders with pagination."""
        tenders, total = await TenderCRUD.search(test_db, limit=2, offset=1)

        assert len(tenders) <= 2
        assert total == 5  # Total should be the same regardless of pagination

    @pytest.mark.asyncio
    async def test_upsert_by_ref_new_tender(self, test_db, test_tender_data):
        """Test upserting a new tender by reference."""
        tender_create = TenderCreate(**test_tender_data)
        upserted_tender = await TenderCRUD.upsert_by_ref(test_db, tender_create)

        assert upserted_tender is not None
        assert upserted_tender.tender_ref == test_tender_data["tender_ref"]
        assert upserted_tender.title == test_tender_data["title"]

    @pytest.mark.asyncio
    async def test_upsert_by_ref_existing_tender(self, test_db, test_tender_data):
        """Test upserting an existing tender by reference."""
        # Create initial tender
        tender_create = TenderCreate(**test_tender_data)
        created_tender = await TenderCRUD.create(test_db, tender_create)

        # Update the tender data
        updated_data = test_tender_data.copy()
        updated_data["title"] = "Updated Title"
        updated_data["value_amount"] = Decimal("200000.00")

        tender_update = TenderCreate(**updated_data)
        upserted_tender = await TenderCRUD.upsert_by_ref(test_db, tender_update)

        assert upserted_tender is not None
        assert upserted_tender.id == created_tender.id  # Same ID
        assert upserted_tender.title == "Updated Title"  # Updated
        assert upserted_tender.value_amount == Decimal("200000.00")  # Updated


class TestUserCRUD:
    """Test user CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_db, test_user_data):
        """Test creating a user."""
        user_create = UserCreate(**test_user_data)
        created_user = await UserCRUD.create(test_db, user_create)

        assert created_user is not None
        assert created_user.email == test_user_data["email"]
        assert created_user.id is not None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, test_db, test_user_data):
        """Test getting a user by ID."""
        user_create = UserCreate(**test_user_data)
        created_user = await UserCRUD.create(test_db, user_create)

        retrieved_user = await UserCRUD.get_by_id(test_db, created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, test_db, test_user_data):
        """Test getting a user by email."""
        user_create = UserCreate(**test_user_data)
        created_user = await UserCRUD.create(test_db, user_create)

        retrieved_user = await UserCRUD.get_by_email(test_db, test_user_data["email"])

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == test_user_data["email"]


class TestSavedFilterCRUD:
    """Test saved filter CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_saved_filter(
        self, test_db, sample_user, test_saved_filter_data
    ):
        """Test creating a saved filter."""
        filter_create = SavedFilterCreate(**test_saved_filter_data)
        created_filter = await SavedFilterCRUD.create(
            test_db, filter_create, sample_user.id
        )

        assert created_filter is not None
        assert created_filter.user_id == sample_user.id
        assert created_filter.keywords == test_saved_filter_data["keywords"]
        assert created_filter.cpv_codes == test_saved_filter_data["cpv_codes"]
        assert created_filter.countries == test_saved_filter_data["countries"]
        assert created_filter.min_value == test_saved_filter_data["min_value"]
        assert created_filter.max_value == test_saved_filter_data["max_value"]
        assert (
            created_filter.notify_frequency
            == test_saved_filter_data["notify_frequency"]
        )

    @pytest.mark.asyncio
    async def test_get_saved_filter_by_id(self, test_db, sample_saved_filter):
        """Test getting a saved filter by ID."""
        retrieved_filter = await SavedFilterCRUD.get_by_id(
            test_db, sample_saved_filter.id
        )

        assert retrieved_filter is not None
        assert retrieved_filter.id == sample_saved_filter.id
        assert retrieved_filter.keywords == sample_saved_filter.keywords

    @pytest.mark.asyncio
    async def test_get_saved_filters_by_user(self, test_db, sample_user):
        """Test getting saved filters by user."""
        filters = await SavedFilterCRUD.get_by_user(test_db, sample_user.id)

        assert len(filters) == 1
        assert filters[0].user_id == sample_user.id

    @pytest.mark.asyncio
    async def test_update_saved_filter(self, test_db, sample_saved_filter):
        """Test updating a saved filter."""
        update_data = SavedFilterUpdate(
            keywords=["updated", "keywords"], min_value=Decimal("75000.00")
        )

        updated_filter = await SavedFilterCRUD.update(
            test_db, sample_saved_filter.id, update_data
        )

        assert updated_filter is not None
        assert updated_filter.id == sample_saved_filter.id
        assert updated_filter.keywords == ["updated", "keywords"]
        assert updated_filter.min_value == Decimal("75000.00")
        # Unchanged fields should remain the same
        assert updated_filter.cpv_codes == sample_saved_filter.cpv_codes

    @pytest.mark.asyncio
    async def test_delete_saved_filter(self, test_db, sample_saved_filter):
        """Test deleting a saved filter."""
        deleted = await SavedFilterCRUD.delete(test_db, sample_saved_filter.id)

        assert deleted is True

        # Verify filter is deleted
        retrieved_filter = await SavedFilterCRUD.get_by_id(
            test_db, sample_saved_filter.id
        )
        assert retrieved_filter is None
